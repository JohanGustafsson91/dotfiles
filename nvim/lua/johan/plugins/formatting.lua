return {
	"stevearc/conform.nvim",
	event = { "BufReadPre", "BufNewFile" },
	config = function()
		local conform = require("conform")

		-- Helper function to check if biome.json exists
		local function has_biome_file()
			local uv = vim.loop
			local cwd = vim.fn.getcwd()
			local biome_path = cwd .. "/biome.json"
			local stat = uv.fs_stat(biome_path)
			return stat ~= nil
		end

		-- Set formatters dynamically based on the existence of biome.json
		local function get_formatters()
			if has_biome_file() then
				return "biome"
			else
				return "prettier"
			end
		end

		-- Configure conform.nvim
		conform.setup({
			formatters = {
				xmllint = {
					command = "xmllint",
					args = { "--format", "-" }, -- Formats XML from stdin
					stdin = true,
				},
			},
			formatters_by_ft = {
				javascript = { get_formatters() },
				typescript = { get_formatters() },
				javascriptreact = { get_formatters() },
				typescriptreact = { get_formatters() },
				svelte = { get_formatters() },
				css = { get_formatters() },
				html = { get_formatters() },
				json = { get_formatters() },
				yaml = { get_formatters() },
				markdown = { get_formatters() },
				graphql = { get_formatters() },
				liquid = { get_formatters() },
				lua = { "stylua" },
				python = { "isort", "black" },
				xml = { "xmllint" },
				xsl = { "xmllint" },
			},
			format_on_save = {
				lsp_fallback = true,
				async = false,
				timeout_ms = 1000,
			},
		})

		-- Keymap for manual formatting
		vim.keymap.set({ "n", "v" }, "<leader>mp", function()
			conform.format({
				lsp_fallback = true,
				async = false,
				timeout_ms = 1000,
			})
		end, { desc = "Format file or range (in visual mode)" })
	end,
}
