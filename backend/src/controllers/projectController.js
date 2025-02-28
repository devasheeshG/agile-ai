const Project = require("../models/Project");

exports.createProject = async (req, res) => {
  try {
    const { name, description } = req.body;
    const newProject = new Project({
      name,
      description,
      owner: req.user.id,
    });
    const project = await newProject.save();
    res.json(project);
  } catch (err) {
    console.error(err.message);
    res.status(500).send("Server error");
  }
};

exports.getAllProjects = async (req, res) => {
  try {
    const projects = await Project.find({ owner: req.user.id });
    res.json(projects);
  } catch (err) {
    console.error(err.message);
    res.status(500).send("Server error");
  }
};

// Implement other project controller methods (getProjectById, updateProject, deleteProject, etc.)
