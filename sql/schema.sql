DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'mountain_pass_status'
    ) THEN
        CREATE TYPE mountain_pass_status AS ENUM ('new', 'pending', 'accepted', 'rejected');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    last_name       VARCHAR(100) NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    middle_name     VARCHAR(100),
    phone           VARCHAR(32) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_users_email_not_blank CHECK (length(trim(email)) > 3),
    CONSTRAINT ck_users_first_name_not_blank CHECK (length(trim(first_name)) > 0),
    CONSTRAINT ck_users_last_name_not_blank CHECK (length(trim(last_name)) > 0),
    CONSTRAINT ck_users_phone_not_blank CHECK (length(trim(phone)) > 0)
);

CREATE TABLE IF NOT EXISTS mountain_passes (
    id              BIGSERIAL PRIMARY KEY,
    beauty_title    VARCHAR(255),
    title           VARCHAR(255) NOT NULL,
    other_titles    VARCHAR(255),
    connect         TEXT,
    add_time        TIMESTAMP NOT NULL,
    status          mountain_pass_status NOT NULL DEFAULT 'new',
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_mountain_passes_title_not_blank CHECK (length(trim(title)) > 0)
);

CREATE TABLE IF NOT EXISTS pass_coordinates (
    id                  BIGSERIAL PRIMARY KEY,
    mountain_pass_id    BIGINT NOT NULL UNIQUE REFERENCES mountain_passes(id) ON DELETE CASCADE,
    latitude            NUMERIC(8, 5) NOT NULL,
    longitude           NUMERIC(8, 5) NOT NULL,
    height              INTEGER NOT NULL,
    CONSTRAINT ck_pass_coordinates_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT ck_pass_coordinates_longitude CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT ck_pass_coordinates_height CHECK (height >= 0)
);

CREATE TABLE IF NOT EXISTS pass_levels (
    id                  BIGSERIAL PRIMARY KEY,
    mountain_pass_id    BIGINT NOT NULL UNIQUE REFERENCES mountain_passes(id) ON DELETE CASCADE,
    winter              VARCHAR(16),
    spring              VARCHAR(16),
    summer              VARCHAR(16),
    autumn              VARCHAR(16)
);

CREATE TABLE IF NOT EXISTS pass_images (
    id                  BIGSERIAL PRIMARY KEY,
    mountain_pass_id    BIGINT NOT NULL REFERENCES mountain_passes(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    image_data          BYTEA NOT NULL,
    content_type        VARCHAR(128),
    position            BIGINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_pass_images_position CHECK (position >= 0),
    CONSTRAINT uq_pass_images_mountain_pass_position UNIQUE (mountain_pass_id, position)
);

CREATE INDEX IF NOT EXISTS ix_mountain_passes_status ON mountain_passes(status);
CREATE INDEX IF NOT EXISTS ix_mountain_passes_add_time ON mountain_passes(add_time);
CREATE INDEX IF NOT EXISTS ix_mountain_passes_user_id ON mountain_passes(user_id);
CREATE INDEX IF NOT EXISTS ix_pass_images_mountain_pass_id ON pass_images(mountain_pass_id);

CREATE OR REPLACE FUNCTION update_mountain_passes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mountain_passes_updated_at ON mountain_passes;

CREATE TRIGGER trg_mountain_passes_updated_at
BEFORE UPDATE ON mountain_passes
FOR EACH ROW
EXECUTE FUNCTION update_mountain_passes_updated_at();
