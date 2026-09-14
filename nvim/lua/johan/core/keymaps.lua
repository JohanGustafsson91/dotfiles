-- set leader key to space
vim.g.mapleader = " "

local keymap = vim.keymap -- for conciseness

-- General Keymaps -------------------
vim.keymap.set("n", "<C-s>", ":w<CR>", { noremap = true, silent = true })
vim.keymap.set("i", "jk", "<Esc>", { noremap = true, silent = true })

-- clear search highlights
keymap.set("n", "<leader>nh", ":nohl<CR>", { desc = "Clear search highlights" })

-- increment/decrement numbers
keymap.set("n", "<leader>+", "<C-a>", { desc = "Increment number" }) -- increment
keymap.set("n", "<leader>-", "<C-x>", { desc = "Decrement number" }) -- decrement

-- window management
keymap.set("n", "<leader>sv", "<cmd>vsplit<CR>", { desc = "Split window vertically" })
keymap.set("n", "<leader>sh", "<cmd>split<CR>", { desc = "Split window horizontally" })
keymap.set("n", "<leader>se", function()
	local cur_win = vim.api.nvim_get_current_win()
	for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
		vim.api.nvim_set_option_value("winfixwidth", false, { win = win })
		vim.api.nvim_set_option_value("winfixheight", false, { win = win })
	end
	vim.cmd("wincmd =")
	vim.api.nvim_set_current_win(cur_win)
end, { desc = "Make splits equal size" })
keymap.set("n", "<leader>sx", "<cmd>close<CR>", { desc = "Close current split" })
keymap.set("n", "<leader>sm", "<C-w>|", { desc = "Maximize current split" })

keymap.set("n", "<leader>to", "<cmd>tabnew<CR>", { desc = "Open new tab" }) -- open new tab
keymap.set("n", "<leader>tx", "<cmd>tabclose<CR>", { desc = "Close current tab" }) -- close current tab
keymap.set("n", "<leader>tn", "<cmd>tabn<CR>", { desc = "Go to next tab" }) --  go to next tab
keymap.set("n", "<leader>tp", "<cmd>tabp<CR>", { desc = "Go to previous tab" }) --  go to previous tab
keymap.set("n", "<leader>tf", "<cmd>tabnew %<CR>", { desc = "Open current buffer in new tab" }) --  move current buffer to new tab

keymap.set("n", "<leader>p", '"0p', { desc = "Paste and keep in buffer" })
keymap.set("n", "<leader><space>", "/", { desc = "Open search" })

-- Buffers (telescope buffer list moved to telescope.lua)
keymap.set("n", "<leader>bn", ":bn<CR>", { desc = "Next buffer" })
keymap.set("n", "<leader>bp", ":bp<CR>", { desc = "Previous buffer" })

keymap.set("n", "<C-u>", "<C-u>zz", {})
keymap.set("n", "<C-d>", "<C-d>zz", {})
keymap.set("n", "<C-b>", "<C-b>zz", {})
keymap.set("n", "<C-f>", "<C-f>zz", {})

-- Folding
keymap.set("n", "<leader>faf", ":g/).*{$/norm! $zf%<CR>", { desc = "Fold all functions" })

-- Center cursor after search movements
keymap.set("n", "n", "nzzzv", { desc = "Next search result (centered)" })
keymap.set("n", "N", "Nzzzv", { desc = "Previous search result (centered)" })
keymap.set("n", "*", "*zzzv", { desc = "Search word under cursor (centered)" })
keymap.set("n", "#", "#zzzv", { desc = "Search word backwards (centered)" })
keymap.set("c", "<CR>", function()
  local cmdtype = vim.fn.getcmdtype()
  if cmdtype == "/" or cmdtype == "?" then
    return "<CR>zz"
  end
  return "<CR>"
end, { expr = true, desc = "Center after search jump" })

-- Open current file in VS Code
vim.keymap.set("n", "<leader>v", function()
	local file = vim.api.nvim_buf_get_name(0)
	if file == "" then
		vim.notify("No file to open", vim.log.levels.WARN)
		return
	end
	local line = vim.fn.line(".")
	local handle = io.popen("git rev-parse --show-toplevel 2>/dev/null")
	local git_root = handle and handle:read("*a") or ""
	handle:close()

	local root = git_root:gsub("%s+$", "") -- trim trailing newline

	if root == "" then
		root = vim.fn.getcwd()
	end

	-- Open VS Code in project root and jump to file:line
	vim.fn.jobstart({ "code", root, "--goto", file .. ":" .. line }, { detach = true })
end, { desc = "Open current project and file in VS Code" })

-- Disable folding in Telescope's result window.
vim.api.nvim_create_autocmd("FileType", { pattern = "TelescopeResults", command = [[setlocal nofoldenable]] })

-- Disable arrow keys in normal mode
keymap.set("n", "<Up>", "<Nop>", { noremap = true, silent = true })
keymap.set("n", "<Down>", "<Nop>", { noremap = true, silent = true })
keymap.set("n", "<Left>", "<Nop>", { noremap = true, silent = true })
keymap.set("n", "<Right>", "<Nop>", { noremap = true, silent = true })

-- Disable arrow keys in insert mode
keymap.set("i", "<Up>", "<Nop>", { noremap = true, silent = true })
keymap.set("i", "<Down>", "<Nop>", { noremap = true, silent = true })
keymap.set("i", "<Left>", "<Nop>", { noremap = true, silent = true })
keymap.set("i", "<Right>", "<Nop>", { noremap = true, silent = true })

-- Disable arrow keys in visual mode
keymap.set("v", "<Up>", "<Nop>", { noremap = true, silent = true })
keymap.set("v", "<Down>", "<Nop>", { noremap = true, silent = true })
keymap.set("v", "<Left>", "<Nop>", { noremap = true, silent = true })
keymap.set("v", "<Right>", "<Nop>", { noremap = true, silent = true })
