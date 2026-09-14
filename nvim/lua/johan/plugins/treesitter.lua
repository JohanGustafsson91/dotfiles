return {
	"nvim-treesitter/nvim-treesitter",
	branch = "main",
	lazy = false,
	build = ":TSUpdate",
	dependencies = {
		"windwp/nvim-ts-autotag",
	},
	config = function()
		-- New main branch API: setup only configures install directory
		require("nvim-treesitter").setup()

		-- Ensure parsers are installed (only installs missing ones)
		local wanted = {
			"json",
			"javascript",
			"typescript",
			"tsx",
			"yaml",
			"html",
			"css",
			"prisma",
			"markdown",
			"markdown_inline",
			"svelte",
			"graphql",
			"bash",
			"lua",
			"vim",
			"dockerfile",
			"gitignore",
			"query",
			"vimdoc",
			"c",
			"java",
			"xml",
		}
		local installed = require("nvim-treesitter").get_installed()
		local installed_set = {}
		for _, p in ipairs(installed) do
			installed_set[p] = true
		end
		local missing = {}
		for _, p in ipairs(wanted) do
			if not installed_set[p] then
				table.insert(missing, p)
			end
		end
		if #missing > 0 then
			require("nvim-treesitter").install(missing)
		end

		-- Enable treesitter highlighting, indentation, and folds per filetype
		vim.api.nvim_create_autocmd("FileType", {
			callback = function(ev)
				-- Start treesitter highlighting (no-op if no parser available)
				local ok = pcall(vim.treesitter.start)
				if not ok then
					return
				end
				-- Treesitter-based indentation (experimental)
				vim.bo[ev.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
				-- Treesitter-based folding
				vim.wo[0][0].foldexpr = "v:lua.vim.treesitter.foldexpr()"
				vim.wo[0][0].foldmethod = "expr"
			end,
		})

		-- autotag setup
		require("nvim-ts-autotag").setup()
	end,
}
