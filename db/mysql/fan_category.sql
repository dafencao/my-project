/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80031
 Source Host           : localhost:3306
 Source Schema         : psad

 Target Server Type    : MySQL
 Target Server Version : 80031
 File Encoding         : 65001

 Date: 21/07/2023 17:33:42
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for fan_category
-- ----------------------------
DROP TABLE IF EXISTS `fan_category`;
CREATE TABLE `fan_category`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `code` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `sort` int NULL DEFAULT NULL,
  `update_at` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `create_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 38 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of fan_category
-- ----------------------------
INSERT INTO `fan_category` VALUES (1, 0, '轴流通风机', '1', 1, '2023-06-15 11:18:10', NULL);
INSERT INTO `fan_category` VALUES (2, 0, '离心通风机', '2', 2, '2023-06-15 11:18:11', NULL);
INSERT INTO `fan_category` VALUES (3, 0, '混流通风机', '3', 3, '2023-06-15 11:18:13', NULL);
INSERT INTO `fan_category` VALUES (4, 3, '轴向离心风机', '4', NULL, '2023-06-08 15:59:59', NULL);
INSERT INTO `fan_category` VALUES (5, 2, '箱型风机', '5', NULL, '2023-06-08 16:00:00', NULL);
INSERT INTO `fan_category` VALUES (6, 2, '标准离心风机', '6', NULL, '2023-06-08 16:00:00', NULL);
INSERT INTO `fan_category` VALUES (7, 2, '无蜗壳离心风机', '7', NULL, '2023-06-08 16:00:01', NULL);
INSERT INTO `fan_category` VALUES (8, 3, '斜流风机', '8', NULL, '2023-06-08 16:00:02', NULL);
INSERT INTO `fan_category` VALUES (9, 1, '前导+后导-轴流风机', '9', NULL, '2023-06-08 16:00:33', NULL);
INSERT INTO `fan_category` VALUES (10, 1, '前导-轴流风机', '10', NULL, '2023-06-08 16:00:35', NULL);
INSERT INTO `fan_category` VALUES (11, 1, '后导-轴流风机', '11', NULL, '2023-06-08 16:00:37', NULL);
INSERT INTO `fan_category` VALUES (12, 2, '外转子离心风机', '12', NULL, '2023-06-08 16:00:39', NULL);
INSERT INTO `fan_category` VALUES (13, 1, '无前后导-轴流风机', '13', NULL, '2023-06-08 16:00:42', NULL);
INSERT INTO `fan_category` VALUES (29, 0, '风机平台', '145', 2, '2023-06-19 10:03:47', '2023-06-15 11:18:04');
INSERT INTO `fan_category` VALUES (36, 3, '超级管理员', '0412', 2, '2023-06-19 10:11:13', '2023-06-19 10:11:13');

SET FOREIGN_KEY_CHECKS = 1;
