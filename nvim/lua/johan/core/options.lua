-- Disable netrw early so it doesn't hijack directory opens (nvim-tree handles this instead)
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

local opt = vim.opt -- for conciseness

-- Line numbers
opt.relativenumber = true -- Show relative line numbers (useful for jumping lines)
opt.number = true -- Show absolute line number on the current line

-- Tabs & indentation
opt.tabstop = 2 -- Number of spaces that a <Tab> in the file counts for
opt.shiftwidth = 2 -- Number of spaces to use for each step of (auto)indent
opt.expandtab = true -- Convert tabs to spaces
opt.autoindent = true -- Copy indent from current line when starting a new one

-- Line wrapping
opt.wrap = false -- Disable line wrapping (long lines won't wrap)

-- Search settings
opt.ignorecase = true -- Ignore case when searching
opt.smartcase = true -- Override ignorecase if search contains uppercase letters

-- Cursor line
opt.cursorline = true -- Highlight the line with the cursor

-- Appearance
opt.termguicolors = true -- Enable 24-bit RGB colors in the TUI (required for some colorschemes)
opt.background = "dark" -- Set background for colorschemes that support it
opt.signcolumn = "yes" -- Always show the sign column (prevents text shifting)

-- Backspace
opt.backspace = "indent,eol,start" -- Allow backspace over everything in insert mode

-- Clipboard
opt.clipboard:append("unnamedplus") -- Use system clipboard as default register

-- Split windows
opt.splitright = true -- Vertical splits open to the right
opt.splitbelow = true -- Horizontal splits open below

-- Swapfile
opt.swapfile = false -- Disable swapfile creation (prevents .swp files)

-- Folding (use treesitter folds but start with everything open)
opt.foldlevel = 99

-- Auto-reload files when changed outside Vim
opt.autoread = true -- Automatically read file when changed outside Vim

-- Trigger autoread when files change on disk
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI" }, {
	pattern = "*",
	command = "if mode() != 'c' | checktime | endif",
})

-- Notification after file change
vim.api.nvim_create_autocmd("FileChangedShellPost", {
	pattern = "*",
	command = "echohl WarningMsg | echo 'File changed on disk. Buffer reloaded.' | echohl None",
})
