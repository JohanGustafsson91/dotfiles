return {
	"iamcco/markdown-preview.nvim",
	cmd = { "MarkdownPreview", "MarkdownPreviewStop", "MarkdownPreviewToggle" },
	ft = { "markdown" },
	build = function(plugin)
		vim.cmd("source " .. vim.fn.fnameescape(plugin.dir .. "/autoload/mkdp/util.vim"))
		vim.fn["mkdp#util#install_sync"]()
	end,
}
