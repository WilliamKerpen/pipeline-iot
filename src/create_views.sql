-- Views reutilizáveis para análises diretas no PostgreSQL.
CREATE OR REPLACE VIEW avg_temp_por_sala AS
SELECT
    room_id_id,
    AVG(temp) AS avg_temp
FROM temperature_readings
GROUP BY room_id_id
ORDER BY room_id_id;

-- Volume de leituras agrupado por hora de ocorrência.
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    DATE_TRUNC('hour', noted_date) AS hora,
    COUNT(*) AS total_leituras
FROM temperature_readings
GROUP BY DATE_TRUNC('hour', noted_date)
ORDER BY hora;

-- Limites diários usados em análises de variação térmica.
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT
    DATE(noted_date) AS dia,
    MAX(temp) AS temp_max,
    MIN(temp) AS temp_min
FROM temperature_readings
GROUP BY DATE(noted_date)
ORDER BY dia;
