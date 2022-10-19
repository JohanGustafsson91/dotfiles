const exec = require("util").promisify(require("child_process").exec);

const MAIN_FOLDER = "[#MAIN#]";

const [pathToCodeFolder] = process.argv.slice(2);
const homeDirRegex = new RegExp(require("os").homedir(), "g");

exec(`tree ${pathToCodeFolder} -L 2 -f -S -F`).then(({ stdout }) => {
  const res = stdout
    .split("\n")
    .reduce((acc, line) => {
      const mainFolder = line.startsWith("��� ");
      const subFolderOrFile = line.includes("���");
      const cleanedName = line.replace(/�/g, "").trim();
      const format = mainFolder
        ? `${MAIN_FOLDER}${cleanedName}`
        : subFolderOrFile
        ? cleanedName
        : "";
      return `${acc}\n${format}`;
    }, "")
    .split(MAIN_FOLDER)
    .map((folder) => {
      const [main, ...subFilesOrFolders] = folder.split("\n").filter(Boolean);
      const mainContainsOnlyFolders = subFilesOrFolders.every((s) =>
        s.endsWith("/")
      );
      return mainContainsOnlyFolders ? subFilesOrFolders : main;
    })
    .flat()
    .map((i) =>
      i.replace(homeDirRegex, "").replace(/\//, "").replace(/\/$/, "")
    )
    .join("\n");

  console.log(res);
});
