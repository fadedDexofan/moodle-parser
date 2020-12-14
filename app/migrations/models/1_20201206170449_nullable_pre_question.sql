##### upgrade #####
ALTER TABLE "question" ALTER COLUMN "pre_question" DROP NOT NULL;
##### downgrade #####
ALTER TABLE "question" ALTER COLUMN "pre_question" SET NOT NULL;
