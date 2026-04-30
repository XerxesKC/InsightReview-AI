-- user 表添加 create_time 字段
ALTER TABLE user ADD COLUMN create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';

-- reply 表不用添加评分字段，如果已添加，则执行以下sql语句删除：
ALTER TABLE reply
DROP COLUMN total_rating,
DROP COLUMN environment_rating,
DROP COLUMN service_rating,
DROP COLUMN taste_rating;