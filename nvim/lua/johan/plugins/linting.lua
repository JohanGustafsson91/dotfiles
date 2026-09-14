return {
	"mfussenegger/nvim-lint",
	event = { "BufReadPre", "BufNewFile" },
	config = function()
		local lint = require("lint")

		local function file_exists(filename)
			local f = io.open(vim.fn.getcwd() .. "/" .. filename, "r")
			if f then
				f:close()
				return true
			end
			return false
		end

		local use_biome = file_exists("biome.json") or file_exists("biome.config.json")

		lint.linters_by_ft = {
			javascript = { use_biome and "biomejs" or "eslint_d" },
			typescript = { use_biome and "biomejs" or "eslint_d" },
			javascriptreact = { use_biome and "biomejs" or "eslint_d" },
			typescriptreact = { use_biome and "biomejs" or "eslint_d" },
			svelte = { use_biome and "biomejs" or "eslint_d" },
			python = { "pylint" },
		}

		local lint_augroup = vim.api.nvim_create_augroup("lint", { clear = true })

		vim.api.nvim_create_autocmd({ "BufEnter", "BufWritePost", "InsertLeave" }, {
			group = lint_augroup,
			callback = function()
				lint.try_lint()
			end,
		})

		vim.keymap.set("n", "<leader>ll", function()
			lint.try_lint()
		end, { desc = "Trigger linting for current file" })
	end,
}
