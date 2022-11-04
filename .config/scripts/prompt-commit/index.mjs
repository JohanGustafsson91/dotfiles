import inquirer from "inquirer";
import util from "util";
import childProcess from "child_process";

const exec = util.promisify(childProcess.exec);

function main() {
  inquirer
    .prompt([
      {
        type: "list",
        name: "commitPrefix",
        message: "What is changed?",
        choices: [
          "feat: Commits, that adds a new feature",
          "fix: Commits, that fixes a bug",
          "refactor: Commits, that rewrite/restructure your code, however does not change any behaviour",
          "perf: Commits are special refactor commits, that improve performance",
          "style: Commits, that do not affect the meaning (white-space, formatting, missing semi-colons, etc)",
          "test: Commits, that add missing tests or correcting existing tests",
          "docs: Commits, that affect documentation only",
          "build: Commits, that affect build components like build tool, ci pipeline, dependencies, project version, ...",
          "ops: Commits, that affect operational components like infrastructure, deployment, backup, recovery, ...",
          "chore: Miscellaneous commits e.g. modifying .gitignore",
        ],
      },
      {
        type: "input",
        name: "commitMessage",
        message: "Enter commit message (imperative)",
      },
      {
        type: "list",
        name: "doCommit",
        message: "Commit now?",
        choices: ["Yes", "No"],
      },
    ])
    .then((answers) => {
      const [prefix] = answers.commitPrefix.split(":");
      const commitMessage = `${prefix}: ${answers.commitMessage}`;

      if (answers.doCommit === "No") {
        console.log("\n" + commitMessage);
        process.exit(1);
      } else {
        exec(`git commit -m "${commitMessage}"`).then(() => process.exit(1));
      }
    });
}

main();
