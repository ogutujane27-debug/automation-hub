"""Load approved automation job definitions."""

from .runtime import AutomationPlatform


def load_jobs(platform: AutomationPlatform) -> AutomationPlatform:
    """Register the platform's approved job definitions."""

    def platform_test(context):
        return {
            "message": "Automation platform execution successful.",
            "run_id": context.run_id,
        }

    platform.register_job(
        name="platform-test",
        description="Safe test of the automation platform runtime.",
        handler=platform_test,
    )

    return platform
