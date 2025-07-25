from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.signing import BadSignature, SignatureExpired
from ninja import Router
from ninja.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from customers.schemas import LoginIn, ProfileOut, RefreshTokenIn, TokenOut
from utils import APIError, CustomerErrorCode, ErrorSchema, SuccessSchema
from utils.auth_bearer import AuthBearer
from utils.email_service import EmailService
from utils.tokens import generate_activation_token, verify_activation_token

UserModel = get_user_model()
customer_router = Router(tags=["customers"])


@customer_router.post(
    "/signup",
    response={200: ProfileOut, 400: ErrorSchema},
    throttle=[UserRateThrottle("5/m")],
    auth=None,
)
def signup(request, data: LoginIn):
    """
    Endpoint for user signup.

    Response codes:
    * 200 OK - Returns the created user profile
    * 400 Bad Request - Error during signup
    """
    if UserModel.objects.filter(email=data.email).exists():
        raise APIError("Email already exists", CustomerErrorCode.EMAIL_EXISTS, 400)

    user = UserModel.objects.create_user(
        username=f"user-{data.email}",
        email=data.email,
        password=data.password,
        is_active=False,
    )
    token = generate_activation_token(user.id)  # Firmar el ID del usuario
    EmailService.send_email(
        subject="Activa tu cuenta",
        to_email=data.email,
        template_name="emails/account_activation.html",
        context={
            "user": user,
            "activation_link": f"{settings.FRONTEND_URL}/activate_account?token={token}",  # Firmar el ID del usuario
        },
    )
    return ProfileOut(
        email=user.email,
    )


@customer_router.post("/login", response={200: TokenOut, 400: ErrorSchema}, auth=None)
def login(request, data: LoginIn):
    try:
        _user = UserModel.objects.get(email=data.email)
        if not _user.is_active:
            raise APIError("User is inactive", CustomerErrorCode.USER_INACTIVE, 400)

        user = authenticate(
            request, username=_user.get_username(), password=data.password
        )
        if not user:
            raise APIError(
                "Credenciales inválidas", CustomerErrorCode.INVALID_CREDENTIALS, 401
            )

        refresh = RefreshToken.for_user(user)
        return TokenOut(
            access=str(refresh.access_token),
            refresh=str(refresh),
            email=user.email,
            first_name=user.first_name,
        )
    except UserModel.DoesNotExist:
        raise APIError("User does not exist", CustomerErrorCode.USER_NOT_FOUND, 400)


@customer_router.get(
    "/profile", response={200: ProfileOut, 401: ErrorSchema}, auth=AuthBearer()
)
def profile(request):
    """
    Endpoint to get the authenticated user's profile.

    Response codes:
    * 200 OK - Returns the user's profile
    * 401 Unauthorized - User not authenticated
    """
    user = request.user
    if not user.is_authenticated:
        raise APIError("User not authenticated", CustomerErrorCode.UNAUTHENTICATED, 401)

    return ProfileOut(
        email=user.email,
    )


@customer_router.post("/refresh-token", response=TokenOut)
def refresh_token(request, data: RefreshTokenIn):
    try:
        refresh = RefreshToken(data.refresh)
        access_token = str(refresh.access_token)

        # Si usás rotación de refresh, generás uno nuevo:
        new_refresh = str(refresh)  # si no hay rotación, podés devolver el mismo

        return TokenOut(access=access_token, refresh=new_refresh)
    except TokenError:
        raise APIError(
            "Refresh token inválido o expirado",
            CustomerErrorCode.REFRESH_TOKEN_INVALID,
            401,
        )


@customer_router.get(
    "/activate-account",
    response={200: SuccessSchema, 400: ErrorSchema, 404: ErrorSchema},
    auth=None,
)
def activate_account(request, token: str):
    try:
        user_id = verify_activation_token(token, 86400)  # 1 día
        user = UserModel.objects.get(pk=user_id)
        user.is_active = True
        user.save()
        return SuccessSchema(
            message="Cuenta activada correctamente. Puedes iniciar sesión ahora.",
            success=True,
        )
    except (BadSignature, SignatureExpired):
        raise APIError(
            "Token inválido o expirado",
            CustomerErrorCode.TOKEN_INVALID,
            400,
        )
    except UserModel.DoesNotExist:
        raise APIError("Usuario no encontrado", CustomerErrorCode.USER_NOT_FOUND, 404)
