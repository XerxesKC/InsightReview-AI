/*
 Navicat Premium Data Transfer

 Source Server         : navicat
 Source Server Type    : MySQL
 Source Server Version : 80041 (8.0.41)
 Source Host           : localhost:3306
 Source Schema         : review_pulse

 Target Server Type    : MySQL
 Target Server Version : 80041 (8.0.41)
 File Encoding         : 65001

 Date: 10/07/2025 16:57:29
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for merchant
-- ----------------------------
DROP TABLE IF EXISTS `merchant`;
CREATE TABLE `merchant`  (
                             `merchant_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '商家主键',
                             `merchant_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '商家名称',
                             `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '商家描述',
                             `category_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '所属子类别 ID',
                             `tag` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '标签',
                             `contact_phone` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '联系电话',
                             `contact_email` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '联系邮箱',
                             `address` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '地址',
                             `cover_image` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '封面图片',
                             `business_license` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '营业执照',
                             `hygienic_license` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '卫生许可证',
                             `verification_status` tinyint NULL DEFAULT NULL COMMENT '认证状态',
                             `business_hours` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '营业时间',
                             `avg_rating` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '平均评分（1~5）',
                             `price_level` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '人均消费',
                             `merchant_status` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '账号状态',
                             `create_time` timestamp NULL DEFAULT NULL COMMENT '创建时间',
                             `update_time` timestamp NULL DEFAULT NULL COMMENT '更新时间',
                             `is_deleted` varchar(1) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '是否删除',
                             `longitude` double NULL DEFAULT NULL COMMENT '商家经度',
                             `latitude` double NULL DEFAULT NULL COMMENT '商家纬度',
                             `merchant_password` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
                             `review` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '审核信息',
                             PRIMARY KEY (`merchant_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci COMMENT = '商家信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of merchant
-- ----------------------------
INSERT INTO `merchant` VALUES ('1', '川香居', '地道川菜，辣而不燥', '6', '川菜', '029-88888888', 'cxj@example.com', '西安市雁塔区小寨东路88号', '/img/cxj.jpg', '/docs/license1.jpg', '/docs/health1.jpg', 2, '10:00-22:00', '4.6', '29', 'active', '2025-07-04 16:34:43', '2025-07-04 16:34:43', 'F', 109.967937, 34.262379, '1', NULL);
INSERT INTO `merchant` VALUES ('10', '孔府家宴餐厅', '高端鲁菜，讲究礼仪', '7', '餐饮,鲁菜,高端', '13800138014', 'kfjyct@example.com', '北京市西城区 XX 大街 14 号', '/img/shandong2.jpg', '/docs/license1014.jpg', '/docs/health1014.jpg', 1, '11:00-22:00', '4.7', '120', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 109.177938, 34.272378, '123456', NULL);
INSERT INTO `merchant` VALUES ('11', '粤味小馆', '地道粤式茶点、小炒', '8', '餐饮,粤菜,茶点', '13800138015', 'ywxg@example.com', '北京市朝阳区 XX 花园 15 号', '/img/guangdong1.jpg', '/docs/license1015.jpg', '/docs/health1015.jpg', 1, '09:00-21:00', '4.6', '70', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 109.167939, 34.282377, '123456', NULL);
INSERT INTO `merchant` VALUES ('12', '岭南风味餐厅', '正宗岭南菜，鲜爽口味', '8', '餐饮,粤菜,岭南', '13800138016', 'lnfwt@example.com', '北京市海淀区 XX 街道 16 号', '/img/guangdong2.jpg', '/docs/license1016.jpg', '/docs/health1016.jpg', 1, '11:00-22:00', '4.5', '90', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 109.1079, 34.292376, '123456', NULL);
INSERT INTO `merchant` VALUES ('13', '香榭丽舍餐厅', '浪漫法式大餐，精致摆盘', '9', '餐饮,西餐,法式', '13800138017', 'xxlsct@example.com', '北京市朝阳区 XX 大道 17 号', '/img/french1.jpg', '/docs/license1017.jpg', '/docs/health1017.jpg', 1, '12:00-22:30', '4.8', '200', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.987931, 34.202375, '123456', NULL);
INSERT INTO `merchant` VALUES ('14', '法式烘焙坊', '现烤法式面包、甜点', '9', '餐饮,西餐,烘焙', '13800138018', 'fsbhf@example.com', '北京市海淀区 XX 广场 18 号', '/img/french2.jpg', '/docs/license1018.jpg', '/docs/health1018.jpg', 1, '08:00-20:00', '4.4', '50', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.967932, 34.212374, '123456', NULL);
INSERT INTO `merchant` VALUES ('15', '罗马假日餐厅', '正宗意大利面、披萨', '10', '餐饮,西餐,意式', '13800138019', 'lmjyrt@example.com', '北京市朝阳区 XX 花园 19 号', '/img/italy1.jpg', '/docs/license1019.jpg', '/docs/health1019.jpg', 1, '11:00-22:00', '4.6', '120', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.957933, 34.222373, '123456', NULL);
INSERT INTO `merchant` VALUES ('16', '威尼斯小馆', '特色意大利菜，环境温馨', '10', '餐饮,西餐,意式', '13800138020', 'wnsxg@example.com', '北京市海淀区 XX 街道 20 号', '/img/italy2.jpg', '/docs/license1020.jpg', '/docs/health1020.jpg', 1, '10:30-21:30', '4.5', '90', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.947934, 34.232372, '123456', NULL);
INSERT INTO `merchant` VALUES ('17', '纽约客餐厅', '美式牛排、汉堡等', '11', '餐饮,西餐,美式', '13800138021', 'nykct@example.com', '北京市朝阳区 XX 大道 21 号', '/img/american1.jpg', '/docs/license1021.jpg', '/docs/health1021.jpg', 1, '11:00-22:00', '4.4', '100', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.937935, 34.242371, '123456', NULL);
INSERT INTO `merchant` VALUES ('18', '加州汉堡店', '巨型汉堡，美式风格', '11', '餐饮,西餐,美式,汉堡', '13800138022', 'jzhbdd@example.com', '北京市海淀区 XX 广场 22 号', '/img/american2.jpg', '/docs/license1022.jpg', '/docs/health1022.jpg', 1, '09:00-21:00', '4.3', '60', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.927936, 34.11237, '123456', NULL);
INSERT INTO `merchant` VALUES ('19', '星光电影院', '多厅放映，新片不断', '12', '娱乐,电影院', '13800138023', 'xgyydy@example.com', '北京市朝阳区 XX 广场 23 号', '/img/cinema1.jpg', '/docs/license1023.jpg', '/docs/health1023.jpg', 1, '09:00-24:00', '4.5', '50', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.917916, 34.122369, '123456', NULL);
INSERT INTO `merchant` VALUES ('2', '不夜城KTV', '豪华包厢，高清音响', '18', 'KTV', '029-66666666', 'ktv@example.com', '西安市高新区科技路38号', '/img/ktv.jpg', '/docs/license2.jpg', '/docs/health2.jpg', 1, '14:00-02:00', '4.2', '20', 'active', '2025-07-04 16:34:43', '2025-07-04 16:34:43', 'F', 108.907926, 34.132368, '1', NULL);
INSERT INTO `merchant` VALUES ('20', '环球影城影院', '高端放映设备，沉浸体验', '12', '娱乐,电影院', '13800138024', 'hqycdy@example.com', '北京市海淀区 XX 大道 24 号', '/img/cinema2.jpg', '/docs/license1024.jpg', '/docs/health1024.jpg', 1, '10:00-23:00', '4.7', '70', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.897936, 34.142367, '123456', NULL);
INSERT INTO `merchant` VALUES ('21', '欢乐游乐场', '大型户外游乐场，多种游乐设施', '2', '娱乐,游乐场', '13800138003', 'hllyc@example.com', '北京市丰台区 XX 路 3 号', '/img/play1.jpg', '/docs/license1003.jpg', '/docs/health1003.jpg', 1, '09:30-18:30', '4.4', '100', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.887946, 34.152366, '123456', NULL);
INSERT INTO `merchant` VALUES ('22', '活力健身房', '专业健身场地，各类健身器材', '2', '娱乐,健身', '13800138004', 'hljsf@example.com', '北京市东城区 XX 胡同 4 号', '/img/gym1.jpg', '/docs/license1004.jpg', '/docs/health1004.jpg', 1, '08:00-22:00', '4.3', '80', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.877956, 34.162365, '123456', NULL);
INSERT INTO `merchant` VALUES ('23', '星空KTV', '豪华包厢，高清音响', '17', '娱乐,KTV', '029-66666666', 'ktv@example.com', '西安市高新区科技路38号', '/img/ktv.jpg', '/docs/license2.jpg', '/docs/health2.jpg', 1, '14:00-02:00', '4.2', '20', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.867966, 34.172364, '123456', NULL);
INSERT INTO `merchant` VALUES ('24', '欢乐迪KTV', '音效出色，服务周到', '16', '娱乐,KTV', '029-77777777', 'hldktv@example.com', '西安市雁塔区小寨西路25号', '/img/ktv2.jpg', '/docs/license25.jpg', '/docs/health25.jpg', 1, '13:00-01:00', '4.3', '25', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.857976, 34.182363, '123456', NULL);
INSERT INTO `merchant` VALUES ('25', '极速网吧', '高速网络，电竞专区', '2', '娱乐,网吧', '029-88888888', 'jswb@example.com', '西安市碑林区友谊东路12号', '/img/netbar.jpg', '/docs/license26.jpg', '/docs/health26.jpg', 1, '24小时营业', '4.1', '15', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.847986, 34.192362, '123456', NULL);
INSERT INTO `merchant` VALUES ('26', '幻影网咖', '高端配置，舒适环境', '2', '娱乐,网吧', '029-99999999', 'hywk@example.com', '西安市莲湖区西大街56号', '/img/netbar2.jpg', '/docs/license27.jpg', '/docs/health27.jpg', 1, '08:00-02:00', '4.4', '20', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.837996, 34.202361, '123456', NULL);
INSERT INTO `merchant` VALUES ('27', '精品服饰店', '时尚潮流服饰，款式多样', '3', '购物,服饰', '13800138005', 'jpfsd@example.com', '北京市西城区 XX 广场 5 号', '/img/cloth1.jpg', '/docs/license1005.jpg', '/docs/health1005.jpg', 1, '10:00-20:00', '4.6', '200', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.827906, 34.09236, '123456', NULL);
INSERT INTO `merchant` VALUES ('28', '数码生活馆', '各类数码产品，正品保障', '3', '购物,数码', '13800138006', 'smshg@example.com', '北京市石景山区 XX 大厦 6 号', '/img/digi1.jpg', '/docs/license1006.jpg', '/docs/health1006.jpg', 1, '09:30-19:30', '4.4', '500', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.817911, 34.082359, '123456', NULL);
INSERT INTO `merchant` VALUES ('29', '家电商场', '家用电器齐全，价格实惠', '3', '购物,家电', '13800138025', 'jdsc@example.com', '北京市朝阳区 XX 路 25 号', '/img/elect1.jpg', '/docs/license1025.jpg', '/docs/health1025.jpg', 1, '09:00-21:30', '4.3', '1500', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.807912, 34.072358, '123456', NULL);
INSERT INTO `merchant` VALUES ('3', '粤香居', '地道粤菜', '8', '粤菜', '029-88886666', 'yxj@example.com', '西安市雁塔区小寨东路87号', '/img/yxj.jpg', '/docs/license3.jpg', '/docs/health3.jpg', 1, '10:00-22:00', '4.8', '30', 'active', '2025-07-06 15:10:52', '2025-07-06 15:10:52', 'F', 108.797913, 34.062357, '1', NULL);
INSERT INTO `merchant` VALUES ('30', '美妆店', '各类化妆品、护肤品', '3', '购物,美妆', '13800138026', 'mzd@example.com', '北京市海淀区 XX 广场 26 号', '/img/makeup.jpg', '/docs/license1026.jpg', '/docs/health1026.jpg', 1, '10:00-21:00', '4.5', '300', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.787914, 34.052356, '123456', NULL);
INSERT INTO `merchant` VALUES ('4', '街角披萨店', '手工现做美味披萨', '4', '餐饮,西餐,披萨', '13800138008', 'jjpszd@example.com', '北京市海淀区 XX 街道 8 号', '/img/pizza1.jpg', '/docs/license1008.jpg', '/docs/health1008.jpg', 1, '10:00-21:00', '4.3', '80', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.747915, 34.042355, '123456', NULL);
INSERT INTO `merchant` VALUES ('5', '老北京面馆', '传统北京炸酱面等特色', '5', '餐饮,中餐,面食', '13800138009', 'lbjmgm@example.com', '北京市东城区 XX 胡同 9 号', '/img/noodle1.jpg', '/docs/license1009.jpg', '/docs/health1009.jpg', 1, '08:30-20:30', '4.5', '40', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.727916, 34.032354, '123456', NULL);
INSERT INTO `merchant` VALUES ('6', '江南菜馆', '精致江南小炒，口味清淡', '5', '餐饮,中餐,江南菜', '13800138010', 'jncyg@example.com', '北京市西城区 XX 路 10 号', '/img/jiangnan1.jpg', '/docs/license1010.jpg', '/docs/health1010.jpg', 1, '11:00-21:00', '4.6', '80', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.876017, 34.022353, '123456', NULL);
INSERT INTO `merchant` VALUES ('7', '辣过瘾川菜馆', '正宗川菜，麻辣够味', '6', '餐饮,川菜,麻辣', '13800138011', 'lgycgc@example.com', '北京市朝阳区 XX 大道 11 号', '/img/sichuan1.jpg', '/docs/license1011.jpg', '/docs/health1011.jpg', 1, '10:30-21:30', '4.4', '70', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.973218, 34.012352, '123456', NULL);
INSERT INTO `merchant` VALUES ('8', '巴山蜀水餐厅', '经典川菜，环境优雅', '6', '餐饮,川菜,特色', '13800138012', 'bssscy@example.com', '北京市海淀区 XX 广场 12 号', '/img/sichuan2.jpg', '/docs/license1012.jpg', '/docs/health1012.jpg', 1, '11:00-22:00', '4.6', '90', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.973119, 34.002351, '123456', NULL);
INSERT INTO `merchant` VALUES ('9', '齐鲁风味馆', '传统鲁菜，量大味足', '7', '餐饮,鲁菜,传统', '13800138013', 'qlfwg@example.com', '北京市丰台区 XX 路 13 号', '/img/shandong1.jpg', '/docs/license1013.jpg', '/docs/health1013.jpg', 1, '10:00-21:00', '4.3', '60', 'active', '2025-07-07 21:46:14', '2025-07-07 21:46:14', 'F', 108.976692, 33.89235, '123456', NULL);

SET FOREIGN_KEY_CHECKS = 1;
