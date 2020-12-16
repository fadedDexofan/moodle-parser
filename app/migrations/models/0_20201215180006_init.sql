##### upgrade #####
CREATE TABLE IF NOT EXISTS "test" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "path" VARCHAR(1024) NOT NULL,
    "test_id" INT NOT NULL,
    "domain" VARCHAR(127) NOT NULL,
    CONSTRAINT "uid_test_test_id_2c6963" UNIQUE ("test_id", "domain")
);
CREATE INDEX IF NOT EXISTS "idx_test_name_0dbe41" ON "test" ("name");
CREATE INDEX IF NOT EXISTS "idx_test_path_b03669" ON "test" ("path");
CREATE INDEX IF NOT EXISTS "idx_test_test_id_2c6963" ON "test" ("test_id", "domain");
CREATE TABLE IF NOT EXISTS "question" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "question_id" INT NOT NULL UNIQUE,
    "screenshot" VARCHAR(256) NOT NULL,
    "status" VARCHAR(17) NOT NULL,
    "test_id" UUID NOT NULL REFERENCES "test" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_question_questio_1f0315" ON "question" ("question_id");
COMMENT ON COLUMN "question"."status" IS 'CORRECT: CORRECT\nPARTIALLY_CORRECT: PARTIALLY_CORRECT\nINCORRECT: INCORRECT';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
