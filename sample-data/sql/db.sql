DROP DATABASE IF EXISTS review_pulse; -- 数据库名不能用中划线-
CREATE DATABASE review_pulse CHARSET utf8;
use review_pulse;

-- 用户表：存储用户基本信息
CREATE TABLE user (
                      user_id VARCHAR(255) NOT NULL COMMENT '用户主键',
                      user_name VARCHAR(255) COMMENT '昵称',
                      phone VARCHAR(255) COMMENT '手机号（可选）',
                      email VARCHAR(255) COMMENT '邮箱（可选）',
                      password VARCHAR(255) COMMENT '密码',
                      avatar VARCHAR(255) COMMENT '头像 URL',
                      gender VARCHAR(1) COMMENT '性别（F/M/O）',
                      birthday VARCHAR(255) COMMENT '出生日期（字符串格式）',
                      show_collection VARCHAR(1) COMMENT '是否公开收藏（T/F）',
                      show_comment VARCHAR(1) COMMENT '是否公开评论（T/F）',
                      user_status VARCHAR(255) COMMENT '账号状态',
                      update_time TIMESTAMP COMMENT '更新时间',
                      is_deleted VARCHAR(1) COMMENT '是否删除',
                      PRIMARY KEY (user_id)
) COMMENT='用户信息表';

-- 商家表：存储商家信息
CREATE TABLE merchant (
                          merchant_id VARCHAR(255) NOT NULL COMMENT '商家主键',
                          merchant_name VARCHAR(255) COMMENT '商家名称',
                          description VARCHAR(255) COMMENT '商家描述',
                          category_id VARCHAR(255) COMMENT '所属子类别 ID',
                          tag VARCHAR(50) COMMENT '标签',
                          contact_phone VARCHAR(255) COMMENT '联系电话',
                          contact_email VARCHAR(255) COMMENT '联系邮箱',
                          address VARCHAR(255) COMMENT '地址',
                          cover_image VARCHAR(255) COMMENT '封面图片',
                          business_license VARCHAR(255) COMMENT '营业执照',
                          hygienic_license VARCHAR(255) COMMENT '卫生许可证',
                          verification_status TINYINT COMMENT '认证状态',
                          business_hours VARCHAR(100) COMMENT '营业时间',
                          avg_rating VARCHAR(255) COMMENT '平均评分（1~5）',
                          price_level VARCHAR(255) COMMENT '人均消费',
                          merchant_status VARCHAR(255) COMMENT '账号状态',
                          create_time TIMESTAMP COMMENT '创建时间',
                          update_time TIMESTAMP COMMENT '更新时间',
                          is_deleted VARCHAR(1) COMMENT '是否删除',
                          PRIMARY KEY (merchant_id)
) COMMENT='商家信息表';

-- 类别表：存储商家分类信息
CREATE TABLE category (
                          category_id VARCHAR(255) NOT NULL COMMENT '类别 ID',
                          category_name VARCHAR(255) COMMENT '类别名称',
                          parent_id VARCHAR(255) COMMENT '父类别 ID（可为 null）',
                          create_time TIMESTAMP COMMENT '创建时间',
                          update_time TIMESTAMP COMMENT '更新时间',
                          is_deleted VARCHAR(1) COMMENT '是否删除',
                          PRIMARY KEY (category_id)
) COMMENT='商家分类表';

-- 收藏表：记录用户收藏的商家
CREATE TABLE favorite (
                          favorite_id VARCHAR(255) NOT NULL COMMENT '主键',
                          user_id VARCHAR(255) COMMENT '用户 ID',
                          merchant_id VARCHAR(255) COMMENT '商家 ID',
                          tag VARCHAR(255) COMMENT '自定义标签（如"常去"）',
                          create_time TIMESTAMP COMMENT '创建时间',
                          update_time TIMESTAMP COMMENT '更新时间',
                          is_deleted VARCHAR(1) COMMENT '是否删除',
                          PRIMARY KEY (favorite_id)
) COMMENT='用户收藏表';

-- 评论表：存储用户对商家的评论
CREATE TABLE comment (
                         comment_id VARCHAR(255) NOT NULL COMMENT '主键',
                         user_id VARCHAR(255) COMMENT '用户 ID',
                         merchant_id VARCHAR(255) COMMENT '商家 ID',
                         comment_content VARCHAR(255) COMMENT '评论内容',
                         is_anonymous VARCHAR(1) COMMENT '是否匿名(Y/N)',
                         rating VARCHAR(255) COMMENT '总评分（1-5）',
                         env_score VARCHAR(255) COMMENT '环境评分',
                         taste_score VARCHAR(255) COMMENT '口味评分',
                         service_score VARCHAR(255) COMMENT '服务评分',
                         status VARCHAR(255) COMMENT '审核状态（待审、通过等）',
                         create_time TIMESTAMP COMMENT '创建时间',
                         update_time TIMESTAMP COMMENT '更新时间',
                         is_deleted VARCHAR(1) COMMENT '是否删除',
                         PRIMARY KEY (comment_id)
) COMMENT='用户评论表';

-- 回复表：存储对评论的回复
CREATE TABLE reply (
                       reply_id VARCHAR(255) NOT NULL COMMENT '主键',
                       comment_id VARCHAR(255) COMMENT '所属评论 ID',
                       user_id VARCHAR(255) COMMENT '回复人 ID',
                       reply_to VARCHAR(255) COMMENT '被回复人 ID（可为 null）',
                       reply_content VARCHAR(255) COMMENT '回复内容',
                       create_time TIMESTAMP COMMENT '创建时间',
                       update_time TIMESTAMP COMMENT '更新时间',
                       is_deleted VARCHAR(1) COMMENT '是否删除',
                       PRIMARY KEY (reply_id)
) COMMENT='评论回复表';

-- 商家动态表：存储商家发布的动态信息
CREATE TABLE MerchantPost (
                              post_id VARCHAR(255) NOT NULL COMMENT '动态ID',
                              merchant_id VARCHAR(255) COMMENT '商家ID',
                              title VARCHAR(255) COMMENT '标题',
                              content VARCHAR(255) COMMENT '内容',
                              create_time TIMESTAMP COMMENT '创建时间',
                              update_time TIMESTAMP COMMENT '更新时间',
                              is_deleted VARCHAR(1) COMMENT '是否删除',
                              PRIMARY KEY (post_id)
) COMMENT='商家动态表';

-- 管理员用户表：存储管理员账户信息
CREATE TABLE admin (
                       admin_id VARCHAR(255) NOT NULL COMMENT '管理员主键',
                       admin_name VARCHAR(255) COMMENT '管理员名称',
                       admin_password VARCHAR(255) COMMENT '管理员密码',
                       create_time TIMESTAMP COMMENT '创建时间',
                       update_time TIMESTAMP COMMENT '更新时间',
                       is_deleted VARCHAR(1) COMMENT '是否删除',
                       PRIMARY KEY (admin_id)
) COMMENT='管理员账户表';
