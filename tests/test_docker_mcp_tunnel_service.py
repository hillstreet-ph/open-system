from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tunnel_client_is_pinned_and_copied_into_runtime_image():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "FROM ghcr.io/openai/tunnel-client:v0.0.15 AS openai_tunnel_client" in dockerfile
    assert "COPY --from=openai_tunnel_client /usr/bin/tunnel-client /usr/local/bin/tunnel-client" in dockerfile


def test_tunnel_service_is_opt_in_and_uses_hermes_stdio_mcp():
    run_script = (ROOT / "docker/s6-rc.d/hermes-mcp-tunnel/run").read_text()

    assert "CONTROL_PLANE_API_KEY" in run_script
    assert "CONTROL_PLANE_TUNNEL_ID" in run_script
    assert 'MCP_COMMAND="${MCP_COMMAND:-hermes mcp serve}"' in run_script
    assert "s6-setuidgid hermes /usr/local/bin/tunnel-client run" in run_script


def test_tunnel_service_is_in_user_bundle():
    bundle_entry = ROOT / "docker/s6-rc.d/user/contents.d/hermes-mcp-tunnel"

    assert bundle_entry.is_file()
