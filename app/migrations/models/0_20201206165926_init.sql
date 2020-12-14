##### upgrade #####
CREATE TABLE IF NOT EXISTS "test" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "test_id" INT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS "idx_test_name_0dbe41" ON "test" ("name");
CREATE INDEX IF NOT EXISTS "idx_test_test_id_fcfeba" ON "test" ("test_id");
CREATE TABLE IF NOT EXISTS "question" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "question_id" VARCHAR(64) NOT NULL UNIQUE,
    "pre_question" VARCHAR(256) NOT NULL,
    "question" VARCHAR(256) NOT NULL,
    "type" VARCHAR(13) NOT NULL,
    "status" VARCHAR(17) NOT NULL,
    "test_id" UUID NOT NULL REFERENCES "test" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_question_questio_1f0315" ON "question" ("question_id");
CREATE INDEX IF NOT EXISTS "idx_question_pre_que_8201fe" ON "question" ("pre_question");
CREATE INDEX IF NOT EXISTS "idx_question_questio_5ab881" ON "question" ("question");
COMMENT ON COLUMN "question"."type" IS 'SINGLE_CHOICE: SINGLE_CHOICE\nMULTI_CHOICE: MULTI_CHOICE\nMULTI_ANSWER: MULTI_ANSWER\nMATCH: MATCH';
COMMENT ON COLUMN "question"."status" IS 'CORRECT: CORRECT\nPARTIALLY_CORRECT: PARTIALLY_CORRECT\nINCORRECT: INCORRECT';
CREATE TABLE IF NOT EXISTS "answer" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "answer" VARCHAR(255) NOT NULL,
    "match_text" VARCHAR(255),
    "match_image" VARCHAR(255),
    "status" VARCHAR(17) NOT NULL,
    "question_id" UUID NOT NULL REFERENCES "question" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "answer"."status" IS 'CORRECT: CORRECT\nPARTIALLY_CORRECT: PARTIALLY_CORRECT\nINCORRECT: INCORRECT';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
