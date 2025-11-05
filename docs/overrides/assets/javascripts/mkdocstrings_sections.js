document.addEventListener("DOMContentLoaded", () => {
  // Target all top-level class or module blocks
  document.querySelectorAll(".doc.doc-object.doc-class, .doc.doc-object.doc-module").forEach(block => {
    const contents =
      block.querySelector(".doc.doc-contents") ||
      block.querySelector(".doc-contents"); // fallback
    const children = block.querySelector(".doc.doc-children");
    if (!contents) return;

    /* ------------------------------------------------------------------
     * Add headers for Signature and Description
     * ------------------------------------------------------------------ */
    const signature = block.querySelector(".doc-signature");
    if (signature && !signature.previousElementSibling?.classList.contains("section-header")) {
      const header = document.createElement("h4");
      header.className = "section-header";
      header.textContent = "Signature:";
      signature.parentNode.insertBefore(header, signature);
    }

    const firstPara = contents.querySelector("p");
    if (firstPara && !firstPara.previousElementSibling?.classList.contains("section-header")) {
      const header = document.createElement("h4");
      header.className = "section-header";
      header.textContent = "Description:";
      contents.insertBefore(header, firstPara);
    }

    const members = contents.querySelector(".doc-children");
    if (members && !members.previousElementSibling?.classList.contains("section-header")) {
      const header = document.createElement("h4");
      header.className = "section-header";
      header.textContent = "Members:";
      contents.insertBefore(header, members);
    }

    if (!children) return;

    /* ------------------------------------------------------------------
     * Collapse and group child elements by type
     * ------------------------------------------------------------------ */
    const sections = [
      { title: "Modules", selector: ".doc.doc-object.doc-module" },
      { title: "Attributes", selector: ".doc.doc-object.doc-attribute" },
      { title: "Methods", selector: ".doc.doc-object.doc-function" },
    ];

    sections.forEach(({ title, selector }) => {
      const elements = Array.from(children.querySelectorAll(selector));
      if (elements.length === 0) return;

      // Create header and collapsible wrapper
      const header = document.createElement("h4");
      header.className = "doc-section-heading";
      header.textContent = title;

      const details = document.createElement("details");
      details.className = "collapse-children";
      details.open = false; // collapsed by default

      const summary = document.createElement("summary");
      summary.textContent = title;

      const container = document.createElement("div");
      container.className = "collapse-children-content";

      elements.forEach(el => container.appendChild(el));

      details.appendChild(summary);
      details.appendChild(container);

      children.insertBefore(details, children.firstChild);
      children.insertBefore(header, details);
    });
  });
});
