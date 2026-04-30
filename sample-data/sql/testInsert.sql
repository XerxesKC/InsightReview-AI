USE review_pulse;
#user 用户表插入数据
INSERT INTO user (user_id, user_name, phone, email, password, avatar, gender, birthday, show_collection, show_comment, user_status, update_time, is_deleted)
VALUES
('u001', 'Alice', '13800000000', 'alice@example.com', 'pass123', '/img/avatar1.jpg', 'F', '1998-05-12', 'T', 'T', 'active', NOW(), 'F'),
('u002', 'Bob', NULL, 'bob@example.com', 'pass456', '/img/avatar2.jpg', 'M', '1995-09-20', 'F', 'T', 'active', NOW(), 'F');

#merchant 商家表插入数据
INSERT INTO merchant (merchant_id, merchant_name, description, category_id, tag, contact_phone, contact_email, address, cover_image, business_license, hygienic_license, verification_status, business_hours, avg_rating, price_level, merchant_status, create_time, update_time, is_deleted)
VALUES
('m001', '川香居', '地道川菜，辣而不燥', 'c001', '川菜', '029-88888888', 'cxj@example.com', '西安市雁塔区小寨东路88号', '/img/cxj.jpg', '/docs/license1.jpg', '/docs/health1.jpg', 1, '10:00-22:00', '4.6', '3', 'active', NOW(), NOW(), 'F'),
('m002', '星空KTV', '豪华包厢，高清音响', 'c003', 'KTV', '029-66666666', 'ktv@example.com', '西安市高新区科技路38号', '/img/ktv.jpg', '/docs/license2.jpg', '/docs/health2.jpg', 1, '14:00-02:00', '4.2', '2', 'active', NOW(), NOW(), 'F');

#category 商家分类表插入数据
INSERT INTO category (category_id, category_name, parent_id, create_time, update_time, is_deleted)
VALUES
('c000', '餐饮', NULL, NOW(), NOW(), 'F'),
('c001', '川菜', 'c000', NOW(), NOW(), 'F'),
('c002', '粤菜', 'c000', NOW(), NOW(), 'F'),
('c003', 'KTV', 'c004', NOW(), NOW(), 'F'),
('c004', '娱乐', NULL, NOW(), NOW(), 'F');


#favorite 收藏表插入数据
INSERT INTO favorite (favorite_id, user_id, merchant_id, tag, create_time, update_time, is_deleted)
VALUES
('f001', 'u001', 'm001', '常去', NOW(), NOW(), 'F'),
('f002', 'u002', 'm002', '待体验', NOW(), NOW(), 'F');

#comment 评论表插入数据
INSERT INTO comment (comment_id, user_id, merchant_id, comment_content, is_anonymous, rating, env_score, taste_score, service_score, status, create_time, update_time, is_deleted)
VALUES
('cmt001', 'u001', 'm001', '菜很正宗，服务热情！', 'N', '5', '5', '5', '5', '通过', NOW(), NOW(), 'F'),
('cmt002', 'u002', 'm002', '音响不错，但有点吵。', 'Y', '4', '4', 'N/A', '4', '通过', NOW(), NOW(), 'F');


#reply 评论回复表插入数据
INSERT INTO reply (reply_id, comment_id, user_id, reply_to, reply_content, create_time, update_time, is_deleted)
VALUES
('r001', 'cmt001', 'u002', 'u001', '我也觉得辣得刚刚好！', NOW(), NOW(), 'F');

#MerchantPost 商家动态表插入数据
INSERT INTO MerchantPost (post_id, merchant_id, title, content, create_time, update_time, is_deleted)
VALUES
('p001', 'm001', '新品上线', '本周推出水煮牛肉、麻辣豆腐等新品，欢迎品尝！', NOW(), NOW(), 'F'),
('p002', 'm002', '夜场优惠', '晚9点后KTV包厢5折优惠，会员专享！', NOW(), NOW(), 'F');

#admin 管理员表插入数据
INSERT INTO admin (admin_id, admin_name, admin_password, create_time, update_time, is_deleted)
VALUES
('a001', 'superadmin', 'admin123', NOW(), NOW(), 'F');
