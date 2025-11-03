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

 Date: 21/07/2023 17:33:28
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for fan_application_model
-- ----------------------------
DROP TABLE IF EXISTS `fan_application_model`;
CREATE TABLE `fan_application_model`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `code` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `update_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `create_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of fan_application_model
-- ----------------------------
INSERT INTO `fan_application_model` VALUES (1, '其他', '1', '2023-05-29 15:45:34', NULL);
INSERT INTO `fan_application_model` VALUES (2, '动车', '2', '2023-05-29 15:45:35', NULL);
INSERT INTO `fan_application_model` VALUES (3, '城轨', '3', '2023-05-29 15:45:35', NULL);
INSERT INTO `fan_application_model` VALUES (4, '机车', '4', '2023-05-29 15:45:37', NULL);

SET FOREIGN_KEY_CHECKS = 1;
