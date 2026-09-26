-- KYLA 0002: security advisor fixes for 0001_kyla_core.sql.
-- Safe to re-run.
--
-- 1) function_search_path_mutable (lint 0011): pin search_path on the updated_at trigger fn.
--    now() lives in pg_catalog, which is always searched, so an empty search_path is fine.
alter function public.kyla_touch_updated_at() set search_path = '';

-- 2) anon/authenticated_security_definer_function_executable (lints 0028 / 0029).
--    kyla_handle_new_user() is only a trigger on auth.users; nobody should call it via /rest/v1/rpc.
--    (Triggers still fire: EXECUTE is not checked when a trigger runs.)
revoke execute on function public.kyla_handle_new_user() from public, anon, authenticated;

--    kyla_is_owner() is used by RLS policies for signed-in users, so `authenticated` keeps
--    EXECUTE (it only reveals the caller's own is_owner flag). Logged-out visitors lose it.
revoke execute on function public.kyla_is_owner() from public, anon;
grant execute on function public.kyla_is_owner() to authenticated;
