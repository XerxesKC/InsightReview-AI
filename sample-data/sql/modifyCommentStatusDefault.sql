-- 把comment表的status字段的默认值改为F
ALTER TABLE `comment`
    MODIFY COLUMN `status` VARCHAR(1) DEFAULT 'F' NOT NULL;