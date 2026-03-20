# **📁 Home Assistant Documentation Structure**

To maintain a "Lean Instance," your documentation should live alongside your YAML. This structure ensures that anyone (including your future self or an AI agent) can understand the system's intent immediately.

## **1\. Recommended Directory Mapping**

/config/  
├── .github/                 \# GitHub Actions (for automated validation)  
├── docs/                    \# 👈 CENTRAL GOVERNANCE  
│   ├── ARCHITECTURE.md      \# The "Why" (System Pillars)  
│   ├── PSPG.md              \# The "How" (Standards & Procedures)  
│   └── diagrams/            \# Mermaid or SVG logic flows  
├── esphome/                 \# ESPHome Node Configs  
│   ├── common/              \# Shared packages (device\_base.yaml)  
│   └── powder-room.yaml     \# Implementation v1.0  
├── blueprints/              \# Shared logic templates  
├── custom\_templates/        \# Jinja2 logic macros  
└── README.md                \# Entry point & Dashboard map

## **2\. GitHub Integration Best Practices**

### **The "Documentation-as-Code" (DaC) Rules:**

1. **README Entry Point:** Your root README.md should contain links to docs/ARCHITECTURE.md and docs/PSPG.md.  
2. **Commit Logic:** When you update a feature (e.g., changing the Backyard Intersection Rule), commit the code changes and the PSPG.md update in the **same commit**. This links the "Law" to the "Execution."  
3. **Internal Linking:** Use relative paths in your Markdown.  
   * *Example:* See \[S-01\](../docs/PSPG.md\#s-01) for enclosure standards.

## **3\. Home Assistant UI Integration**

You can actually pull these Markdown files directly into your Home Assistant Dashboard using a **Markdown Card**.

### **Example Configuration Card:**

type: markdown  
content: \>  
  \#\# 📘 System Governance  
  \*\*Current Posture:\*\* {{ states('sensor.house\_posture') }}  
    
  \*\*Quick Links:\*\*  
  \- \[View Architecture\](https://github.com/your-repo/blob/main/docs/ARCHITECTURE.md)  
  \- \[View Compliance Checklist\](https://github.com/your-repo/blob/main/docs/PSPG.md)

## **4\. Why this works for the "Lean Instance"**

* **Zero Latency:** Documentation is available locally via the "File Editor" or "VS Code" addons.  
* **Agent Friendly:** If you ever use an AI to help troubleshoot, you can point it to the /docs/ folder, and it will immediately understand your label\_entities logic and area\_key naming conventions.