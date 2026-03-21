-- Verificacion de persistencia de evaluaciones y scores
-- Uso: ejecutar en el SQL Editor de Supabase

-- 1) Ultimas evaluaciones con columnas criticas
select
  e.id,
  e.song_id,
  s.title,
  s.artist,
  e.total_score,
  e.score_objectification,
  e.score_roles,
  e.score_possession,
  e.score_degrading,
  e.evidence_objectification,
  e.evidence_roles,
  e.evidence_degrading,
  e.dominant_narrative,
  e.evaluated_at
from llm_evaluations e
left join songs s on s.id = e.song_id
order by e.id desc
limit 25;

-- 2) Deteccion de filas con score=0 pero NO inconclusas (sospechosas)
select
  e.id,
  e.song_id,
  s.title,
  s.artist,
  e.total_score,
  e.dominant_narrative,
  e.evaluated_at
from llm_evaluations e
left join songs s on s.id = e.song_id
where e.total_score = 0
  and coalesce(e.dominant_narrative, '') not ilike 'Inconcluso%'
order by e.id desc
limit 50;

-- 3) Deteccion de filas con evidencia vacia en narrativas NO inconclusas (sospechosas)
select
  e.id,
  e.song_id,
  s.title,
  s.artist,
  e.total_score,
  e.dominant_narrative,
  e.evidence_objectification,
  e.evidence_roles,
  e.evidence_degrading,
  e.evaluated_at
from llm_evaluations e
left join songs s on s.id = e.song_id
where coalesce(e.dominant_narrative, '') not ilike 'Inconcluso%'
  and (
    e.evidence_objectification is null
    and e.evidence_roles is null
    and e.evidence_degrading is null
  )
order by e.id desc
limit 50;

-- 4) Conteo de inconclusas vs concluyentes en las ultimas N filas
with ultimas as (
  select *
  from llm_evaluations
  order by id desc
  limit 200
)
select
  count(*) as total,
  count(*) filter (where coalesce(dominant_narrative, '') ilike 'Inconcluso%') as inconclusas,
  count(*) filter (where coalesce(dominant_narrative, '') not ilike 'Inconcluso%') as concluyentes
from ultimas;

-- 5) Ultima evaluacion por cancion para seguimiento operativo
with ranked as (
  select
    e.*, row_number() over (partition by e.song_id order by e.id desc) as rn
  from llm_evaluations e
)
select
  r.id,
  r.song_id,
  s.title,
  s.artist,
  r.total_score,
  r.dominant_narrative,
  r.evaluated_at
from ranked r
left join songs s on s.id = r.song_id
where r.rn = 1
order by r.id desc
limit 100;

-- 6) Sanity-check de una cancion especifica (reemplazar :song_id)
-- select
--   e.id,
--   e.song_id,
--   e.total_score,
--   e.score_objectification,
--   e.score_roles,
--   e.score_possession,
--   e.score_degrading,
--   e.evidence_objectification,
--   e.evidence_roles,
--   e.evidence_degrading,
--   e.dominant_narrative,
--   e.evaluated_at
-- from llm_evaluations e
-- where e.song_id = :song_id
-- order by e.id desc
-- limit 20;
