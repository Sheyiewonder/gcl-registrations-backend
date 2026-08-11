from brevo import AsyncBrevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)

from app.core.config import settings


brevo_client = AsyncBrevo(
    api_key=settings.BREVO_API_KEY,
)


async def send_email(
    to: str | list[str],
    subject: str,
    html: str,
):
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = to

    result = await brevo_client.transactional_emails.send_transac_email(
        sender=SendTransacEmailRequestSender(
            email=settings.EMAIL_FROM,
            name=settings.EMAIL_FROM_NAME,
        ),
        to=[
            SendTransacEmailRequestToItem(email=email)
            for email in recipients
        ],
        subject=subject,
        html_content=html,
    )

    return result


async def send_admin_otp_email(
    email: str,
    otp: str,
    expires_minutes: int,
):
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background:#f5f7fa; padding:40px;">
    <div style="
        max-width:600px;
        margin:auto;
        background:white;
        padding:40px;
        border-radius:12px;
    ">
        <h2>Admin Verification</h2>

        <p>
            Use the verification code below to complete your
            administrator login.
        </p>

        <div style="
            font-size:32px;
            font-weight:bold;
            letter-spacing:8px;
            text-align:center;
            padding:20px;
            margin:25px 0;
            background:#f1f5f9;
            border-radius:8px;
        ">
            {otp}
        </div>

        <p>
            This code expires in
            <strong>{expires_minutes} minutes</strong>.
        </p>

        <p>
            If you did not attempt to sign in, you can safely
            ignore this email.
        </p>
    </div>
</body>
</html>
"""

    return await send_email(
        to=email,
        subject="Your Admin Verification Code",
        html=html,
    )


async def send_admin_invitation_email(
    email: str,
    invitation_token: str,
    expires_hours: int,
):
    setup_url = (
        f"{settings.FRONTEND_URL}"
        f"/admin/setup-password"
        f"?token={invitation_token}"
    )

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background:#f5f7fa; padding:40px;">
    <div style="
        max-width:600px;
        margin:auto;
        background:white;
        padding:40px;
        border-radius:12px;
    ">
        <h2>You're Invited as an Administrator</h2>

        <p>
            You have been invited to become an administrator
            on the registration platform.
        </p>

        <p>
            Click the button below to create your password
            and activate your account.
        </p>

        <div style="text-align:center; margin:30px 0;">
            <a
                href="{setup_url}"
                style="
                    display:inline-block;
                    padding:14px 24px;
                    background:#1F3875;
                    color:white;
                    text-decoration:none;
                    border-radius:8px;
                    font-weight:bold;
                "
            >
                Set Up Your Password
            </a>
        </div>

        <p>
            This invitation expires in
            <strong>{expires_hours} hours</strong>.
        </p>

        <p>
            If you were not expecting this invitation,
            you can safely ignore this email.
        </p>
    </div>
</body>
</html>
"""

    return await send_email(
        to=email,
        subject="Administrator Invitation",
        html=html,
    )

async def send_admin_password_reset_email(
    email: str,
    reset_token: str,
    expires_minutes: int,
):
    reset_url = (
        f"{settings.FRONTEND_URL}"
        f"/admin/reset-password"
        f"?token={reset_token}"
    )

    html = f"""
    <div>
        <p>
            We received a request to reset the password
            for your administrator account.
        </p>

        <p>
            Click the button below to create a new password.
        </p>

        <div style="text-align:center; margin:30px 0;">
            <a
                href="{reset_url}"
                style="
                    display:inline-block;
                    padding:14px 24px;
                    background:#1F3875;
                    color:white;
                    text-decoration:none;
                    border-radius:8px;
                    font-weight:bold;
                "
            >
                Reset Your Password
            </a>
        </div>

        <p>
            This link expires in
            <strong>{expires_minutes} minutes</strong>.
        </p>

        <p>
            If you did not request a password reset,
            you can safely ignore this email.
        </p>
    </div>
    """

    return await send_email(
        to=email,
        subject="Reset Your Administrator Password",
        html=html,
    )