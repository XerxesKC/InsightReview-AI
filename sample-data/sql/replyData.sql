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

 Date: 10/07/2025 17:02:49
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for reply
-- ----------------------------
DROP TABLE IF EXISTS `reply`;
CREATE TABLE `reply`  (
                          `reply_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '主键',
                          `comment_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '所属评论 ID',
                          `user_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '回复人 ID',
                          `reply_to` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '被回复人 ID（可为 null）',
                          `reply_content` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                          `create_time` timestamp NULL DEFAULT NULL COMMENT '创建时间',
                          `update_time` timestamp NULL DEFAULT NULL COMMENT '更新时间',
                          `is_deleted` varchar(1) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '是否删除',
                          PRIMARY KEY (`reply_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci COMMENT = '评论回复表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of reply
-- ----------------------------
INSERT INTO `reply` VALUES ('1', '1', '2', '1', '我也觉得辣得刚刚好！😊', '2025-07-04 16:34:43', '2025-07-04 16:34:43', 'F');
INSERT INTO `reply` VALUES ('1942863833980899329', '15', '1', '2', '1233333', '2025-07-09 16:30:09', '2025-07-09 16:30:09', 'F');
INSERT INTO `reply` VALUES ('1942864395161997313', '15', '1', '2', '124436456', '2025-07-09 16:32:23', '2025-07-09 16:32:23', 'F');
INSERT INTO `reply` VALUES ('1943111102902784001', '19', '1', '3', 'e2432wef23r', '2025-07-10 08:52:43', '2025-07-10 08:52:43', 'F');
INSERT INTO `reply` VALUES ('1943117040514715649', '19', '1', '3', '2342', '2025-07-10 09:16:18', '2025-07-10 09:16:18', 'F');

SET FOREIGN_KEY_CHECKS = 1;
