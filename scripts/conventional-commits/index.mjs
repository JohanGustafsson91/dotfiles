import util from "util";
import childProcess from "child_process";

const exec = util.promisify(childProcess.exec);

async function main() {
  const commitPrefixChoice = await promptQuestionWithSelectableAnswer(
    "What type of change are you committing?",
    [
      "feat: A new feature",
      "fix: A bug fix",
      "docs: Documentation only changes",
      "style: Changes that do not affect the meaning of the code (white-space, formatting, etc)",
      "refactor: A code change that neither fixes a bug nor adds a feature",
      "perf: A code change that improves performance",
      "test: Adding missing tests or correcting existing tests",
      "build: Changes that affect the build system or external dependencies",
      "ci: Changes to CI configuration files and scripts",
      "chore: Other changes that don’t modify src or test files",
      "revert: Reverts a previous commit",
    ],
  );

  const [prefix] = commitPrefixChoice.split(":");

  const commitMessage = await promptQuestion(
    `Enter commit message (imperative) for "${prefix}":`,
  );

  const doCommitChoice = await promptQuestionWithYesNoAnswer("Commit now?");

  const finalCommitMessage = `${prefix}: ${commitMessage}`;

  if (doCommitChoice === "n") {
    console.log("\n" + finalCommitMessage);
    process.exit(1);
  } else {
    exec(`git commit -m "${finalCommitMessage}"`)
      .then(() => {
        console.log("Commit successful!");
        process.exit(1);
      })
      .catch((error) => {
        console.error("Error during commit:", error);
        process.exit(1);
      });
  }
}

function promptQuestionWithSelectableAnswer(question, options) {
  return new Promise((resolve) => {
    console.log(`\n${question}`);
    options.forEach((option, index) => {
      console.log(`${index + 1}: ${option}`);
    });

    process.stdout.write(`\n Choose an option (1-${options.length}): `);
    process.stdin.once("data", (data) => {
      const choice = parseInt(data.toString().trim(), 10);
      if (choice >= 1 && choice <= options.length) {
        return resolve(options[choice - 1]);
      } else {
        console.log("Invalid choice, please try again.");
        return resolve(promptQuestionWithSelectableAnswer(question, options));
      }
    });
  });
}

function promptQuestion(question) {
  return new Promise((resolve) => {
    console.log(`\n${question}`);
    process.stdin.once("data", resolve);
  });
}

function promptQuestionWithYesNoAnswer(question) {
  return new Promise((resolve) => {
    process.stdout.write(`\n${question} (y/n): `);
    process.stdin.once("data", (data) => {
      const answer = data.toString().trim().toLowerCase();
      if (answer === "y" || answer === "n") {
        return resolve(answer);
      } else {
        console.log("Invalid choice, please enter 'y' or 'n'.");
        return resolve(promptQuestionWithYesNoAnswer(question));
      }
    });
  });
}

main();
