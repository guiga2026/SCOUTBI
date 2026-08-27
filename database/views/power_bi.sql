-- Gold views for Power BI. Apply after the core tables exist.
CREATE OR REPLACE VIEW vw_matches AS
SELECT
    f.id AS fixture_id,
    f.date::date AS match_date,
    f.date AS match_datetime,
    f.competition_id,
    c.name AS competition_name,
    f.season_id,
    s.year AS season_year,
    f.home_team_id,
    home_team.name AS home_team_name,
    f.away_team_id,
    away_team.name AS away_team_name,
    f.status,
    f.round,
    f.home_goals,
    f.away_goals,
    CASE WHEN f.home_goals > f.away_goals THEN 'H' WHEN f.home_goals = f.away_goals THEN 'D' WHEN f.home_goals < f.away_goals THEN 'A' END AS result
FROM fixtures f
LEFT JOIN competitions c ON c.id = f.competition_id
LEFT JOIN seasons s ON s.id = f.season_id
LEFT JOIN teams home_team ON home_team.id = f.home_team_id
LEFT JOIN teams away_team ON away_team.id = f.away_team_id;

CREATE OR REPLACE VIEW vw_team_performance AS
WITH match_rows AS (
    SELECT home_team_id AS team_id, competition_id, season_id, home_goals AS goals_for, away_goals AS goals_against,
           CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS wins,
           CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END AS draws,
           CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END AS losses,
           CASE WHEN away_goals = 0 THEN 1 ELSE 0 END AS clean_sheets
    FROM fixtures WHERE status IN ('FT', 'AET', 'PEN')
    UNION ALL
    SELECT away_team_id, competition_id, season_id, away_goals, home_goals,
           CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END,
           CASE WHEN home_goals = 0 THEN 1 ELSE 0 END
    FROM fixtures WHERE status IN ('FT', 'AET', 'PEN')
)
SELECT mr.competition_id, c.name AS competition_name, mr.season_id, s.year AS season_year,
       mr.team_id, t.name AS team_name, COUNT(*) AS matches, SUM(wins) AS wins, SUM(draws) AS draws,
       SUM(losses) AS losses, SUM(goals_for) AS goals_for, SUM(goals_against) AS goals_against,
       SUM(goals_for - goals_against) AS goal_difference, SUM(wins * 3 + draws) AS points,
       SUM(clean_sheets) AS clean_sheets,
       ROUND(AVG(goals_for)::numeric, 2) AS goals_per_match,
       ROUND(AVG(goals_against)::numeric, 2) AS conceded_per_match
FROM match_rows mr
LEFT JOIN competitions c ON c.id = mr.competition_id
LEFT JOIN seasons s ON s.id = mr.season_id
LEFT JOIN teams t ON t.id = mr.team_id
GROUP BY mr.competition_id, c.name, mr.season_id, s.year, mr.team_id, t.name;

CREATE OR REPLACE VIEW vw_standings AS
SELECT st.competition_id, c.name AS competition_name, st.season_id, s.year AS season_year,
       st.team_id, t.name AS team_name, st.position, st.played, st.wins, st.draws, st.losses,
       st.goals_for, st.goals_against, st.points
FROM standings st
LEFT JOIN competitions c ON c.id = st.competition_id
LEFT JOIN seasons s ON s.id = st.season_id
LEFT JOIN teams t ON t.id = st.team_id;

CREATE OR REPLACE VIEW vw_data_quality AS
SELECT endpoint, status_code, collected_at, jsonb_array_length(payload::jsonb) AS rows_collected
FROM raw_ingestions;

CREATE OR REPLACE VIEW vw_fixture_events AS
SELECT e.fixture_id, f.date::date AS match_date, e.time_minute, e.type, e.detail,
       e.team_id, t.name AS team_name, e.player_id, p.name AS player_name
FROM fixture_events e
LEFT JOIN fixtures f ON f.id = e.fixture_id
LEFT JOIN teams t ON t.id = e.team_id
LEFT JOIN players p ON p.id = e.player_id;

CREATE OR REPLACE VIEW vw_fixture_statistics AS
SELECT s.fixture_id, f.date::date AS match_date, s.team_id, t.name AS team_name,
       s.metric, s.value
FROM fixture_statistics s
LEFT JOIN fixtures f ON f.id = s.fixture_id
LEFT JOIN teams t ON t.id = s.team_id;

CREATE OR REPLACE VIEW vw_player_statistics AS
SELECT ps.fixture_id, f.date::date AS match_date, ps.player_id, p.name AS player_name,
       ps.team_id, t.name AS team_name, ps.metric, ps.value
FROM player_statistics ps
LEFT JOIN fixtures f ON f.id = ps.fixture_id
LEFT JOIN players p ON p.id = ps.player_id
LEFT JOIN teams t ON t.id = ps.team_id;

CREATE OR REPLACE VIEW vw_metric_definitions AS
SELECT metric_key, version, name, category, source_type, formula, methodology, active
FROM metric_definitions;

CREATE OR REPLACE VIEW vw_player_features AS
SELECT pf.player_id, p.name AS player_name, pf.team_id, t.name AS team_name,
       pf.competition_id, c.name AS competition_name, pf.season_id, s.year AS season_year,
       pf.metric_key, pf.metric_version, pf.value, pf.sample_size, pf.confidence, pf.source_type
FROM player_season_features pf
LEFT JOIN players p ON p.id = pf.player_id
LEFT JOIN teams t ON t.id = pf.team_id
LEFT JOIN competitions c ON c.id = pf.competition_id
LEFT JOIN seasons s ON s.id = pf.season_id;

CREATE OR REPLACE VIEW vw_player_score_components AS
SELECT sc.player_id, p.name AS player_name, sc.competition_id, c.name AS competition_name,
       sc.season_id, s.year AS season_year, sc.position_model, sc.metric_key,
       sc.metric_version, sc.raw_value, sc.normalized_value, sc.weight, sc.contribution,
       sc.explanation
FROM player_score_components sc
LEFT JOIN players p ON p.id = sc.player_id
LEFT JOIN competitions c ON c.id = sc.competition_id
LEFT JOIN seasons s ON s.id = sc.season_id;

CREATE OR REPLACE VIEW vw_player_scores AS
SELECT ps.player_id, p.name AS player_name, ps.competition_id, c.name AS competition_name,
       ps.season_id, s.year AS season_year, ps.position_model, ps.metric_version,
       ps.score, ps.confidence, ps.explanation, ps.source_type
FROM player_scores ps
LEFT JOIN players p ON p.id = ps.player_id
LEFT JOIN competitions c ON c.id = ps.competition_id
LEFT JOIN seasons s ON s.id = ps.season_id;
