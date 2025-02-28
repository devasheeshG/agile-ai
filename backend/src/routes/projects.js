const express = require("express");
const router = express.Router();
const projectController = require("../controllers/projectController");

router.post("/", projectController.createProject);
router.get("/", projectController.getAllProjects);
router.get("/:id", projectController.getProjectById);
router.put("/:id", projectController.updateProject);
router.delete("/:id", projectController.deleteProject);
router.post("/:id/members", projectController.addProjectMember);
router.delete(
  "/:id/members/:userId",
  authMiddleware,
  projectController.removeProjectMember
);

module.exports = router;
