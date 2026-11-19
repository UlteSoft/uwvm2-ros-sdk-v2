# @file presym.rb
# @brief Invoke the upstream symbol table generator on the target's preprocessed core sources.
source, build, *units = ARGV
require File.join(source, "lib/mruby/presym")
require "fileutils"
class String
  def relative_path
    self
  end
end
class MRuby::Presym
  def _pp(*_args)
  end
end
generator = MRuby::Presym.new(Struct.new(:build_dir).new(build))
FileUtils.mkdir_p(generator.header_dir)
symbols = generator.scan(units)
generator.write_id_header(symbols)
generator.write_table_header(symbols)
