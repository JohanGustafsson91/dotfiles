return {
	"NvChad/nvim-colorizer.lua", -- Updated to maintained fork
	event = { "BufReadPre", "BufNewFile" },
	opts = {
		filetypes = { "css", "javascript", "typescript", "html" },
		user_default_options = {
			rgb_fn = true,
			tailwind = true, -- Enable tailwind colors
			css = true,
			names = false, -- Don't highlight color names like "red"
		},
	},
}
