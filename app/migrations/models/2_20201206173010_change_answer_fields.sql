##### upgrade #####
ALTER TABLE "answer" ALTER COLUMN "answer" TYPE TEXT;
ALTER TABLE "answer" ALTER COLUMN "match_text" TYPE TEXT;
##### downgrade #####
ALTER TABLE "answer" ALTER COLUMN "answer" TYPE VARCHAR(255);
ALTER TABLE "answer" ALTER COLUMN "match_text" TYPE VARCHAR(255);
