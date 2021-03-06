#
# Copyright 2019 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Seeds module."""
import concurrent.futures
import logging
from functools import partial

from django.db import connections

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def on_complete(completed_log_message, future):
    """Explicitly close the connection for the thread."""
    connections.close_all()
    logger.info(completed_log_message)


def role_seeding():
    """Update any roles at startup."""
    # noqa: E402 pylint: disable=C0413
    from api.models import Tenant
    from management.role.definer import seed_roles
    from rbac.settings import MAX_SEED_THREADS

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SEED_THREADS) as executor:
            tenants = Tenant.objects.all()
            tenant_count = tenants.count()
            for idx, tenant in enumerate(list(tenants)):
                if tenant.schema_name != "public":
                    logger.info(f"Seeding role changes for tenant {tenant.schema_name} [{idx + 1} of {tenant_count}].")
                    future = executor.submit(seed_roles, tenant, update=True)
                    completed_log_message = (
                        "Finished seeding role changes for tenant "
                        f"{tenant.schema_name} [{idx + 1} of {tenant_count}]."
                    )
                    future.add_done_callback(partial(on_complete, completed_log_message))
    except Exception as exc:
        logger.error(f"Error encountered during role seeding {exc}.")


def group_seeding():
    """Update platform group at startup."""
    # noqa: E402 pylint: disable=C0413
    from api.models import Tenant
    from management.group.definer import seed_group
    from rbac.settings import MAX_SEED_THREADS

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SEED_THREADS) as executor:
            tenants = Tenant.objects.all()
            tenant_count = tenants.count()
            for idx, tenant in enumerate(list(tenants)):
                if tenant.schema_name != "public":
                    logger.info(
                        f"Seeding group changes for tenant {tenant.schema_name} [{idx + 1} of {tenant_count}]."
                    )
                    future = executor.submit(seed_group, tenant)
                    completed_log_message = (
                        "Finished seeding group changes for tenant "
                        f"{tenant.schema_name} [{idx + 1} of {tenant_count}]."
                    )
                    future.add_done_callback(partial(on_complete, completed_log_message))
    except Exception as exc:
        logger.error(f"Error encountered during group seeding {exc}.")
