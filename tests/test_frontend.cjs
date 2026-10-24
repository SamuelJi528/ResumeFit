const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function workspace() {
  const nodes = new Map();
  function node(selector) {
    if (!nodes.has(selector)) {
      nodes.set(selector, {
        value: "", checked: true, disabled: false,
        classList: { toggle() {} },
        addEventListener() {}, setAttribute() {},
      });
    }
    return nodes.get(selector);
  }
  const context = vm.createContext({
    document: {
      querySelector: node,
      querySelectorAll(selector) {
        if (selector === ".refine-button" || selector === ".refine-input") {
          return [node(selector)];
        }
        return [];
      },
    },
  });
  const source = fs.readFileSync(path.join(__dirname, "../public/static/app.js"), "utf8");
  // Exercise UI state synchronously without making startup network requests.
  vm.runInContext(source.replace(/\ninitialize\(\);\s*$/, ""), context);
  vm.runInContext(`
    resumeInput.value = "Original resume";
    jobInput.value = "Original job";
    state.inputs = currentInputs();
    state.result = {};
    state.ready = true;
  `, context);
  return { node, run: (code) => vm.runInContext(code, context) };
}

test("editing review inputs disables refinement fields and buttons", () => {
  const { node, run } = workspace();
  run('resumeInput.value = "Changed resume"; updateInputs();');
  assert.equal(node(".refine-button").disabled, true);
  assert.equal(node(".refine-input").disabled, true);
});

test("restoring reviewed inputs re-enables refinement after an upload", () => {
  const { node, run } = workspace();
  run('resumeInput.value = "Changed resume"; setBusy(false, "upload");');
  assert.equal(node(".refine-input").disabled, true);
  run('resumeInput.value = "Original resume"; updateInputs();');
  assert.equal(node(".refine-button").disabled, false);
  assert.equal(node(".refine-input").disabled, false);
});
