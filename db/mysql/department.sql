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

 Date: 21/07/2023 17:33:20
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for department
-- ----------------------------
DROP TABLE IF EXISTS `department`;
CREATE TABLE `department`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `parent_id` int NULL DEFAULT NULL COMMENT '父级id',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '部门名称',
  `code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '部门编码',
  `sort` int NULL DEFAULT NULL,
  `create_by` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `create_at` timestamp NULL DEFAULT NULL,
  `update_by` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `update_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 42 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of department
-- ----------------------------
INSERT INTO `department` VALUES (1, 0, '湖南联诚轨道装备有限公司', 'A101', 1, NULL, '2023-05-23 18:23:46', NULL, '2023-06-19 09:21:45');
INSERT INTO `department` VALUES (2, 1, '株洲联诚集团控股股份有限公司', 'A102', 1, NULL, '2023-05-23 18:23:43', NULL, '2023-05-23 15:27:31');
INSERT INTO `department` VALUES (3, 2, '集团公司领导', 'A103', 1, NULL, '2023-05-23 18:23:40', NULL, '2023-05-23 15:46:22');
INSERT INTO `department` VALUES (4, 2, '后勤服务中心', 'A104', 2, NULL, '2023-05-23 18:23:32', NULL, '2023-05-23 15:37:34');
INSERT INTO `department` VALUES (5, 1, '湖南联诚轨道装备有限公司', 'A105', 2, NULL, '2023-05-23 18:23:36', NULL, '2023-05-26 14:30:46');
INSERT INTO `department` VALUES (6, 2, '规划发展部', 'A106', 3, NULL, '2023-05-23 18:23:29', NULL, '2023-05-23 18:23:26');
INSERT INTO `department` VALUES (7, 2, '人力资源部', 'A107', 4, NULL, '2023-05-23 18:24:26', NULL, '2023-05-23 18:24:29');
INSERT INTO `department` VALUES (8, 2, '财务资产部', 'A108', 5, NULL, '2023-05-23 18:25:02', NULL, '2023-05-23 18:25:04');
INSERT INTO `department` VALUES (9, 2, '技术中心', 'A109', 6, NULL, '2023-05-23 18:25:29', NULL, '2023-05-23 18:25:31');
INSERT INTO `department` VALUES (10, 2, '智能与数据研发部', 'A110', 7, NULL, '2023-05-23 18:26:03', NULL, '2023-05-23 18:26:05');

SET FOREIGN_KEY_CHECKS = 1;
