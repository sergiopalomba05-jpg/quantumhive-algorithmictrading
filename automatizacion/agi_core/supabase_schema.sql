-- Supabase Schema para AGI Telegram
-- Ejecutar este script en el SQL Editor de Supabase

-- 1. Tabla conversaciones (historial de chat)
CREATE TABLE IF NOT EXISTS conversaciones (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rol TEXT NOT NULL CHECK (rol IN ('user', 'assistant')),
    contenido TEXT NOT NULL,
    tipo_mensaje TEXT DEFAULT 'texto'
);

-- Índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_conversaciones_fecha ON conversaciones(fecha DESC);

-- 2. Tabla ideas (ideas de Sergio)
CREATE TABLE IF NOT EXISTS ideas (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT,
    score INTEGER,
    notas TEXT,
    estado TEXT DEFAULT 'registrada'
);

CREATE INDEX IF NOT EXISTS idx_ideas_fecha ON ideas(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_categoria ON ideas(categoria);

-- 3. Tabla mensajes (compatibilidad con código existente)
CREATE TABLE IF NOT EXISTS mensajes (
    id BIGSERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    tipo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    respuesta TEXT,
    guardado_en_vision BOOLEAN DEFAULT FALSE,
    score_viabilidad REAL
);

CREATE INDEX IF NOT EXISTS idx_mensajes_timestamp ON mensajes(timestamp DESC);

-- 4. Tabla metricas
CREATE TABLE IF NOT EXISTS metricas (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    categoria TEXT,
    nombre TEXT NOT NULL,
    valor REAL,
    unidad TEXT,
    fuente TEXT
);

CREATE INDEX IF NOT EXISTS idx_metricas_fecha ON metricas(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_metricas_categoria ON metricas(categoria);

-- 5. Tabla alertas
CREATE TABLE IF NOT EXISTS alertas (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tipo TEXT NOT NULL,
    severidad TEXT,
    descripcion TEXT,
    estado TEXT DEFAULT 'activa'
);

CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_estado ON alertas(estado);

-- 6. Tabla decisiones
CREATE TABLE IF NOT EXISTS decisiones (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    descripcion TEXT NOT NULL,
    tipo TEXT,
    impacto TEXT,
    ejecutada_por TEXT,
    resultado TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisiones_fecha ON decisiones(fecha DESC);

-- 7. Tabla agentes
CREATE TABLE IF NOT EXISTS agentes (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    division TEXT,
    estado TEXT DEFAULT 'activo',
    score_reputacion REAL DEFAULT 50.0
);

CREATE INDEX IF NOT EXISTS idx_agentes_estado ON agentes(estado);

-- Habilitar Row Level Security (RLS) para seguridad
ALTER TABLE conversaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensajes ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE decisiones ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (permitir todo por ahora, se puede restringir después)
-- Drop policies first if they exist (for idempotent script)
DROP POLICY IF EXISTS "Permitir todo en conversaciones" ON conversaciones;
DROP POLICY IF EXISTS "Permitir todo en ideas" ON ideas;
DROP POLICY IF EXISTS "Permitir todo en mensajes" ON mensajes;
DROP POLICY IF EXISTS "Permitir todo en metricas" ON metricas;
DROP POLICY IF EXISTS "Permitir todo en alertas" ON alertas;
DROP POLICY IF EXISTS "Permitir todo en decisiones" ON decisiones;
DROP POLICY IF EXISTS "Permitir todo en agentes" ON agentes;

CREATE POLICY "Permitir todo en conversaciones" ON conversaciones FOR ALL USING (true);
CREATE POLICY "Permitir todo en ideas" ON ideas FOR ALL USING (true);
CREATE POLICY "Permitir todo en mensajes" ON mensajes FOR ALL USING (true);
CREATE POLICY "Permitir todo en metricas" ON metricas FOR ALL USING (true);
CREATE POLICY "Permitir todo en alertas" ON alertas FOR ALL USING (true);
CREATE POLICY "Permitir todo en decisiones" ON decisiones FOR ALL USING (true);
CREATE POLICY "Permitir todo en agentes" ON agentes FOR ALL USING (true);
