return {
	"stevearc/conform.nvim",
	event = { "BufReadPre", "BufNewFile" },
	config = function()
		local conform = require("conform")

		-- Resolve each buffer independently, stopping at its nearest Git root.
		local function get_formatters(bufnr)
			local filename = vim.api.nvim_buf_get_name(bufnr)
			if filename == "" then
				return { "prettier" }
			end
			local directory = vim.fs.dirname(filename)
			while directory do
				for _, name in ipairs({ "biome.json", "biome.jsonc" }) do
					local stat = vim.uv.fs_stat(directory .. "/" .. name)
					if stat and stat.type == "file" then
						return { "biome" }
					end
				end
				if vim.uv.fs_stat(directory .. "/.git") then
					break
				end
				local parent = vim.fs.dirname(directory)
				if parent == directory then
					break
				end
				directory = parent
			end
			return { "prettier" }
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
				javascript = get_formatters,
				typescript = get_formatters,
				javascriptreact = get_formatters,
				typescriptreact = get_formatters,
				svelte = get_formatters,
				css = get_formatters,
				html = get_formatters,
				json = get_formatters,
				yaml = get_formatters,
				markdown = get_formatters,
				graphql = get_formatters,
				liquid = get_formatters,
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
