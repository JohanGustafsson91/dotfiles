return {
	"nvim-neotest/neotest",
	dependencies = {
		"nvim-neotest/nvim-nio",
		"nvim-lua/plenary.nvim",
		"antoinemadec/FixCursorHold.nvim",
		"nvim-treesitter/nvim-treesitter",
		"nvim-neotest/neotest-python",
		"marilari88/neotest-vitest",
		"nvim-neotest/neotest-jest",
	},
	keys = {
		{ "<leader>rt", function() require("neotest").run.run() end, desc = "Run nearest test" },
		{ "<leader>rT", function() require("neotest").run.run(vim.fn.expand("%")) end, desc = "Run test file" },
		{ "<leader>ra", function() require("neotest").run.run(vim.fn.getcwd()) end, desc = "Run all tests" },
		{ "<leader>rl", function() require("neotest").run.run_last() end, desc = "Run last test" },
		{ "<leader>rs", function() require("neotest").summary.toggle() end, desc = "Toggle test summary" },
		{ "<leader>ro", function() require("neotest").output.open({ enter = true }) end, desc = "Show test output" },
		{ "<leader>rO", function() require("neotest").output_panel.toggle() end, desc = "Toggle output panel" },
		{ "<leader>rx", function() require("neotest").run.stop() end, desc = "Stop test" },
	},
	config = function()
		require("neotest").setup({
			adapters = {
				require("neotest-vitest"),
				require("neotest-jest"),
				require("neotest-python")({
					dap = { justMyCode = false },
				}),
			},
			floating = {
				border = "rounded",
				max_height = 0.6,
				max_width = 0.6,
			},
			icons = {
				running_animated = { "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏" },
			},
		})
	end,
}
