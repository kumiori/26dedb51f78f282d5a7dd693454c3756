from examples.minimal_consumer.consumer import build_team_network


def test_independent_consumer() -> None:
    projection = build_team_network()
    assert [item.id for item in projection.nodes] == ["host", "guest"]
