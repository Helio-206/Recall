ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;

UPDATE public.alembic_version
SET version_num = '202607290002';
