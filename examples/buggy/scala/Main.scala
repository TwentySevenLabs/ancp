import does.not.Exist

object Main {
  def main(args: Array[String]): Unit = {
    val count: Int = "bad"
    println(missingSymbol)
    takesTwo(1)
  }

  def takesTwo(a: Int, b: Int): Int = a + b
}

