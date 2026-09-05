"""Node service transactions and repository SQL, without PostgreSQL or SQLite."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compute_node import ComputeNode
from app.models.enums import NodeHealth, NodeReachability
from app.repositories.node_repository import NodeRepository
from app.schemas.node import ComputeNodeCreate, ComputeNodeUpdate
from app.services.node_service import NodeAlreadyExistsError, NodeNotFoundError, NodeService


@pytest.fixture
def session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def service(session):
    service = NodeService(session)
    service.repository = AsyncMock(spec=NodeRepository)
    service.repository.get_by_name.return_value = None
    return service


@pytest.fixture
def node():
    return ComputeNode(
        id=uuid4(),
        name="JORGE",
        endpoint="http://127.0.0.1:8000",
        credential_ref="jorge-agent",
        enabled=True,
        reachability=NodeReachability.ONLINE,
        observed_health=NodeHealth.HEALTHY,
    )


@pytest.fixture
def data():
    return ComputeNodeCreate(name="JORGE", endpoint="http://localhost:8000", credential_ref="ref")


async def test_create_persists_and_commits(service, session, node, data):
    service.repository.create.return_value = node
    assert await service.create_node(data) is node
    service.repository.get_by_name.assert_awaited_once_with("JORGE")
    service.repository.create.assert_awaited_once_with(**data.model_dump())
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_duplicate_create(service, session, node, data):
    service.repository.get_by_name.return_value = node
    with pytest.raises(NodeAlreadyExistsError):
        await service.create_node(data)
    service.repository.create.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


@pytest.mark.parametrize("operation", ["get", "update"])
async def test_missing_node(service, operation):
    service.repository.get_by_id.return_value = None
    with pytest.raises(NodeNotFoundError):
        if operation == "get":
            await service.get_node(uuid4())
        else:
            await service.update_node(uuid4(), ComputeNodeUpdate(enabled=False))
    service.repository.update.assert_not_awaited()


async def test_duplicate_update(service, session, node):
    service.repository.get_by_id.return_value = node
    service.repository.get_by_name.return_value = ComputeNode(id=uuid4(), name="OTHER")
    with pytest.raises(NodeAlreadyExistsError):
        await service.update_node(node.id, ComputeNodeUpdate(name="OTHER"))
    service.repository.update.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


async def test_same_name_is_allowed_and_only_supplied_fields_are_written(service, session, node):
    service.repository.get_by_id.return_value = node
    service.repository.update.return_value = node
    assert await service.update_node(node.id, ComputeNodeUpdate(name=node.name)) is node
    service.repository.get_by_name.assert_not_awaited()
    service.repository.update.assert_awaited_once_with(node, name=node.name)
    session.commit.assert_awaited_once()


async def test_disable_preserves_observations(session, node):
    service = NodeService(session)
    session.scalar.return_value = node
    result = await service.update_node(node.id, ComputeNodeUpdate(enabled=False))
    assert result.enabled is False
    assert result.reachability == NodeReachability.ONLINE
    assert result.observed_health == NodeHealth.HEALTHY
    assert result.name == "JORGE"
    session.commit.assert_awaited_once()


def integrity_error(constraint, sqlstate):
    driver_error = Exception("private database details")
    driver_error.constraint_name = constraint
    original = Exception("adapter")
    original.sqlstate = sqlstate
    original.__cause__ = driver_error
    return IntegrityError("statement", {}, original)


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("failure_at", ["flush", "commit"])
@pytest.mark.parametrize(
    ("constraint", "sqlstate", "expected"),
    [
        ("uq_compute_nodes_name", "23505", NodeAlreadyExistsError),
        ("another_unique_index", "23505", IntegrityError),
        ("uq_compute_nodes_name", "23514", IntegrityError),
        (None, "23505", IntegrityError),
    ],
)
async def test_integrity_errors(
    service, session, node, data, operation, failure_at, constraint, sqlstate, expected
):
    service.repository.get_by_id.return_value = node
    error = integrity_error(constraint, sqlstate)
    target = session.commit if failure_at == "commit" else getattr(service.repository, operation)
    target.side_effect = error
    with pytest.raises(expected) as caught:
        if operation == "create":
            await service.create_node(data)
        else:
            await service.update_node(node.id, ComputeNodeUpdate(name="NEW"))
    if expected is IntegrityError:
        assert caught.value is error
    session.rollback.assert_awaited_once()


async def test_repository_create_flushes_without_commit(session, data):
    node = await NodeRepository(session).create(**data.model_dump())
    session.add.assert_called_once_with(node)
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()
    assert node.name == data.name
    assert node.credential_ref == data.credential_ref
    assert node.endpoint == data.endpoint
    assert node.enabled is True


async def test_list_uses_database_name_order_and_no_commit(session, node):
    result = MagicMock()
    result.all.return_value = [node]
    session.scalars.return_value = result
    assert await NodeService(session).list_nodes() == [node]
    statement = session.scalars.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert sql.endswith("ORDER BY compute_nodes.name")
    session.commit.assert_not_awaited()
    session.flush.assert_not_awaited()


@pytest.mark.parametrize("lookup", ["get_by_id", "get_by_name"])
async def test_repository_lookup(session, node, lookup):
    session.scalar.return_value = node
    value = node.id if lookup == "get_by_id" else node.name
    assert await getattr(NodeRepository(session), lookup)(value) is node
    compiled = session.scalar.call_args.args[0].compile(dialect=postgresql.dialect())
    assert value in compiled.params.values()
    assert "WHERE compute_nodes." in str(compiled)
    session.commit.assert_not_awaited()
