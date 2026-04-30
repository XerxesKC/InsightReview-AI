-- 评论图片关联表
CREATE TABLE `comment_images` (
                                  `comment_images_id` VARCHAR(255) PRIMARY KEY,
                                  `comment_id` VARCHAR(255) NOT NULL, -- 在这里设置字符集和排序规则
                                  `url` VARCHAR(255) NOT NULL,
                                  `is_deleted` VARCHAR(1) DEFAULT 'F' COMMENT '是否删除(T/F)',
                                  `create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                  `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);

-- 评论视频关联表 (同理)
CREATE TABLE `comment_videos` (
                                  `comment_videos_id` VARCHAR(255) PRIMARY KEY,
                                  `comment_id` VARCHAR(255) NOT NULL,
                                  `url` VARCHAR(255) NOT NULL,
                                  `is_deleted` VARCHAR(1) DEFAULT 'F' COMMENT '是否删除(T/F)',
                                  `create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                  `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);