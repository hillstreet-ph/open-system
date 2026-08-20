// Ingest verified backup metadata from CI / operators (no binary upload here).
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("method not allowed", { status: 405 });
  }
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) {
    return new Response(JSON.stringify({ ok: false, error: "missing env" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
  const payload = await req.json();
  const supabase = createClient(url, key);
  const row = {
    backup_id: payload.backup_id,
    git_sha: payload.git_sha ?? null,
    image_digest: payload.image_digest ?? null,
    verification_status: payload.verification_status ?? "UNVERIFIED",
    notes: payload.notes ?? null,
    storage_uri: payload.storage_uri ?? null,
    checksum_sha256: payload.checksum_sha256 ?? null,
  };
  const { error } = await supabase.from("open_system_backup_catalog").upsert(row, {
    onConflict: "backup_id",
  });
  if (error) {
    return new Response(JSON.stringify({ ok: false, error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
  await supabase.from("open_system_sync_events").insert({
    source: "edge",
    event_type: "backup_catalog_ingest",
    payload: row,
  });
  return new Response(JSON.stringify({ ok: true }), {
    headers: { "Content-Type": "application/json" },
  });
});
