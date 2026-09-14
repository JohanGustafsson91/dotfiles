return {
	"nvim-telescope/telescope.nvim",
	branch = "master",
	dependencies = {
		"nvim-lua/plenary.nvim",
		{ "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
		"nvim-tree/nvim-web-devicons",
	},
	config = function()
		local telescope = require("telescope")
		local actions = require("telescope.actions")

		local current_path_display = "smart"

		local function toggle_path_display()
			current_path_display = (current_path_display == "smart") and "absolute" or "smart"
			print("Telescope path display set to: " .. current_path_display)
		end

		telescope.setup({
			defaults = {
				path_display = function(_, path)
					if current_path_display == "absolute" then
						return path
					end
					-- smart: show only filename, but include parent if ambiguous
					local tail = require("telescope.utils").path_tail(path)
					return tail
				end,
				mappings = {
					i = {
						["<C-k>"] = actions.move_selection_previous,
						["<C-j>"] = actions.move_selection_next,
						["<C-q>"] = actions.send_to_qflist + actions.open_qflist,
					},
				},
			},
		pickers = {
			live_grep = {
				additional_args = function()
					return {
						"--hidden",
						"--glob", "!.git/*",
						"--glob", "!node_modules/*",
						"--glob", "!dist/*",
						"--glob", "!build/*",
						"--glob", "!target/*",
						"--glob", "!vendor/*",
						"--glob", "!.next/*",
					}
				end,
			},
			find_files = {
				hidden = true,
				find_command = {
					"rg", "--files", "--hidden",
					"--glob", "!.git/*",
					"--glob", "!node_modules/*",
					"--glob", "!dist/*",
					"--glob", "!build/*",
					"--glob", "!target/*",
					"--glob", "!vendor/*",
					"--glob", "!.next/*",
				},
			},
		},
		})

		telescope.load_extension("fzf")

		-- set keymaps
		local keymap = vim.keymap -- for conciseness

		keymap.set("n", "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Fuzzy find files in cwd" })
		keymap.set("n", "<leader>fr", "<cmd>Telescope oldfiles<cr>", { desc = "Fuzzy find recent files" })
		keymap.set("n", "<leader>fs", "<cmd>Telescope live_grep<cr>", { desc = "Find string in cwd" })
		keymap.set("n", "<leader>fl", "<cmd>Telescope resume<cr>", { desc = "Find resume" })
		keymap.set("n", "<leader>fc", "<cmd>Telescope grep_string<cr>", { desc = "Find string under cursor in cwd" })
		keymap.set("n", "<leader>fd", "<cmd>Telescope diagnostics<cr>", { desc = "Find diagnostics" })
		
		-- Git keymaps
		keymap.set("n", "<leader>fgs", "<cmd>Telescope git_status<cr>", { desc = "Git status" })
		keymap.set("n", "<leader>fgb", "<cmd>Telescope git_branches<cr>", { desc = "Git branches" })
		keymap.set("n", "<leader>fgc", "<cmd>Telescope git_commits<cr>", { desc = "Git commits" })
		
		-- Buffer management
		keymap.set("n", "<leader>bl", "<cmd>Telescope buffers<cr>", { desc = "List buffers" })

		keymap.set("n", "<leader>ftp", function()
			toggle_path_display()
		end, { desc = "Toggle Telescope path display" })
	end,
}
