module.exports = [
  {
    type: "heading",
    defaultValue: "Spider Fam"
  },
  {
    type: "text",
    defaultValue:
      "One family per day, or preview mode cycling all families every 3 seconds."
  },
  {
    type: "toggle",
    messageKey: "ColorSpider",
    label: "Color illustrations",
    description:
      "When on, uses full-color art. When off, uses a grayscale plate style.",
    defaultValue: true
  },
  {
    type: "toggle",
    messageKey: "PreviewCycle",
    label: "Preview all families (3 sec)",
    description:
      "Advances through each family every 3 seconds (ignores daily rotation).",
    defaultValue: false
  },
  {
    type: "select",
    messageKey: "DarkBackground",
    label: "Background",
    defaultValue: "0",
    options: [
      { label: "White (default)", value: "0" },
      { label: "Black", value: "1" }
    ]
  },
  {
    type: "submit",
    defaultValue: "Save"
  }
];