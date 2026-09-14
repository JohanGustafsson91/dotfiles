return {
	"sindrets/diffview.nvim",
	dependencies = { "nvim-lua/plenary.nvim" },
	cmd = { "DiffviewOpen", "DiffviewFileHistory" },
	keys = {
		{ "<leader>gd", "<cmd>DiffviewOpen<cr>", desc = "Open git diff view" },
		{ "<leader>gc", "<cmd>DiffviewClose<cr>", desc = "Close git diff view" },
		{ "<leader>gh", "<cmd>DiffviewFileHistory %<cr>", desc = "File history" },
		{ "<leader>gH", "<cmd>DiffviewFileHistory<cr>", desc = "Branch history" },
	},
	opts = {
		enhanced_diff_hl = true, -- See ':h diffview-config-enhanced_diff_hl'
		view = {
			default = {
				layout = "diff2_horizontal", -- Use horizontal split
			},
			file_history = {
				layout = "diff2_horizontal",
			},
		},
		keymaps = {
			file_panel = {
				{
					"n",
					"<cr>",
					function()
						require("diffview.actions").focus_entry()
						vim.schedule(function()
							vim.cmd("wincmd l")
						end)
					end,
					{ desc = "Open the diff and focus right panel" },
				},
				{
					"n",
					"o",
					function()
						require("diffview.actions").focus_entry()
						vim.schedule(function()
							vim.cmd("wincmd l")
						end)
					end,
					{ desc = "Open the diff and focus right panel" },
				},
				{
					"n",
					"l",
					function()
						require("diffview.actions").focus_entry()
						vim.schedule(function()
							vim.cmd("wincmd l")
						end)
					end,
					{ desc = "Open the diff and focus right panel" },
				},
			},
		},
	},
}
