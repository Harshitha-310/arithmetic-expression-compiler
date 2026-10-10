#include <cctype>
#include <climits>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <sstream>

struct Node {
    enum class Kind { Number, Unary, Binary } kind;
    long long value = 0;
    char op = 0;
    std::unique_ptr<Node> left, right;
    explicit Node(long long n) : kind(Kind::Number), value(n) {}
    Node(char oper, std::unique_ptr<Node> child)
        : kind(Kind::Unary), op(oper), left(std::move(child)) {}
    Node(char oper, std::unique_ptr<Node> lhs, std::unique_ptr<Node> rhs)
        : kind(Kind::Binary), op(oper), left(std::move(lhs)), right(std::move(rhs)) {}
};

class Parser {
    std::string input;
    size_t pos = 0;
    void skipSpaces() {
        while (pos < input.size() && std::isspace(static_cast<unsigned char>(input[pos]))) ++pos;
    }
    bool consume(char c) {
        skipSpaces();
        if (pos < input.size() && input[pos] == c) { ++pos; return true; }
        return false;
    }
    std::unique_ptr<Node> expression() {
        auto n = term();
        while (true) {
            if (consume('+')) n = std::make_unique<Node>('+', std::move(n), term());
            else if (consume('-')) n = std::make_unique<Node>('-', std::move(n), term());
            else break;
        }
        return n;
    }
    std::unique_ptr<Node> term() {
        auto n = unary();
        while (true) {
            if (consume('*')) n = std::make_unique<Node>('*', std::move(n), unary());
            else if (consume('/')) n = std::make_unique<Node>('/', std::move(n), unary());
            else if (consume('%')) n = std::make_unique<Node>('%', std::move(n), unary());
            else break;
        }
        return n;
    }
    std::unique_ptr<Node> unary() {
        if (consume('+')) return std::make_unique<Node>('+', unary());
        if (consume('-')) return std::make_unique<Node>('-', unary());
        return primary();
    }
    std::unique_ptr<Node> primary() {
        skipSpaces();
        if (consume('(')) {
            auto n = expression();
            if (!consume(')')) throw std::runtime_error("Syntax error: expected ')' ");
            return n;
        }
        skipSpaces();
        if (pos >= input.size() || !std::isdigit(static_cast<unsigned char>(input[pos])))
            throw std::runtime_error("Syntax error: expected an integer or '('");
        long long value = 0;
        while (pos < input.size() && std::isdigit(static_cast<unsigned char>(input[pos]))) {
            int digit = input[pos++] - '0';
            if (value > (LLONG_MAX - digit) / 10) throw std::runtime_error("Integer literal overflow");
            value = value * 10 + digit;
        }
        return std::make_unique<Node>(value);
    }
public:
    explicit Parser(std::string s) : input(std::move(s)) {}
    std::unique_ptr<Node> parse() {
        auto n = expression();
        skipSpaces();
        if (pos != input.size())
            throw std::runtime_error(std::string("Syntax error: unexpected character '") + input[pos] + "'");
        return n;
    }
};

long long checkedAdd(long long a, long long b) {
    if ((b > 0 && a > LLONG_MAX - b) || (b < 0 && a < LLONG_MIN - b))
        throw std::runtime_error("Integer overflow");
    return a + b;
}

long long checkedSub(long long a, long long b) {
    if ((b < 0 && a > LLONG_MAX + b) || (b > 0 && a < LLONG_MIN + b))
        throw std::runtime_error("Integer overflow");
    return a - b;
}

long long checkedMul(long long a, long long b) {
    if (a == 0 || b == 0) return 0;
    if ((a == -1 && b == LLONG_MIN) || (b == -1 && a == LLONG_MIN))
        throw std::runtime_error("Integer overflow");
    if (a > 0) {
        if ((b > 0 && a > LLONG_MAX / b) || (b < 0 && b < LLONG_MIN / a))
            throw std::runtime_error("Integer overflow");
    } else {
        if ((b > 0 && a < LLONG_MIN / b) || (b < 0 && a < LLONG_MAX / b))
            throw std::runtime_error("Integer overflow");
    }
    return a * b;
}

long long eval(const Node& n) {
    if (n.kind == Node::Kind::Number) return n.value;
    if (n.kind == Node::Kind::Unary) {
        long long x = eval(*n.left);
        if (n.op == '+') return x;
        if (x == LLONG_MIN) throw std::runtime_error("Integer overflow");
        return -x;
    }
    long long a = eval(*n.left), b = eval(*n.right);
    switch (n.op) {
        case '+': return checkedAdd(a, b);
        case '-': return checkedSub(a, b);
        case '*': return checkedMul(a, b);
        case '/':
            if (b == 0) throw std::runtime_error("Runtime error: division by zero");
            if (a == LLONG_MIN && b == -1) throw std::runtime_error("Integer overflow");
            return a / b; // C++ integer division truncates toward zero.
        case '%':
            if (b == 0) throw std::runtime_error("Runtime error: modulo by zero");
            if (a == LLONG_MIN && b == -1) throw std::runtime_error("Integer overflow");
            return a % b; // Remainder follows C++ sign rules.
        default: throw std::runtime_error("Internal error: unknown operator");
    }
}

std::unique_ptr<Node> optimize(std::unique_ptr<Node> n) {
    if (n->kind == Node::Kind::Number) return n;
    n->left = optimize(std::move(n->left));
    if (n->kind == Node::Kind::Binary) n->right = optimize(std::move(n->right));
    if (n->kind == Node::Kind::Unary && n->left->kind == Node::Kind::Number) {
        long long v = n->left->value;
        if (n->op == '+') return std::make_unique<Node>(v);
        if (v != LLONG_MIN) return std::make_unique<Node>(-v);
    }
    if (n->kind == Node::Kind::Binary && n->left->kind == Node::Kind::Number && n->right->kind == Node::Kind::Number) {
        try { return std::make_unique<Node>(eval(*n)); }
        catch (const std::exception&) { /* Keep expressions whose evaluation raises an error. */ }
    }
    return n;
}

std::string emitIR(const Node& n, std::vector<std::string>& lines, int& temp) {
    if (n.kind == Node::Kind::Number) return std::to_string(n.value);
    if (n.kind == Node::Kind::Unary) {
        std::string a = emitIR(*n.left, lines, temp);
        if (n.op == '+') return a;
        std::string out = "%t" + std::to_string(temp++);
        lines.push_back(out + " = neg " + a);
        return out;
    }
    std::string a = emitIR(*n.left, lines, temp), b = emitIR(*n.right, lines, temp);
    std::string out = "%t" + std::to_string(temp++);
    std::string opname = n.op == '+' ? "add" : n.op == '-' ? "sub" : n.op == '*' ? "mul" : n.op == '/' ? "div" : "mod";
    lines.push_back(out + " = " + opname + " " + a + ", " + b);
    return out;
}

void printTokens(const std::string& s) {
    std::cout << "TOKENS:\n";
    for (size_t i = 0; i < s.size();) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        if (std::isspace(c)) { ++i; continue; }
        if (std::isdigit(c)) {
            size_t j = i;
            while (j < s.size() && std::isdigit(static_cast<unsigned char>(s[j]))) ++j;
            std::cout << "  INT(" << s.substr(i, j - i) << ")\n";
            i = j;
        } else if (std::string("+-*/%()").find(s[i]) != std::string::npos) {
            std::cout << "  " << s[i] << "\n"; ++i;
        } else { std::cout << "  INVALID(" << s[i] << ")\n"; ++i; }
    }
}

int main(int argc, char** argv) {
    bool all = false, showTokens = false, showIR = false, doOptimize = false, resultOnly = false;
    std::string expression;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--all") all = true;
        else if (arg == "--tokens") showTokens = true;
        else if (arg == "--ir") showIR = true;
        else if (arg == "--optimize") doOptimize = true;
        else if (arg == "--result") resultOnly = true;
        else if (arg == "--version") { std::cout << "MiniCompiler Verification Edition 1.1\n"; return 0; }
        else if (arg == "--help" || arg == "-h") {
            std::cout << "MiniCompiler Verification Edition\n"
                      << "Usage: minicompiler [OPTIONS] \"EXPRESSION\"\n"
                      << "  --result    Print only the computed integer result\n"
                      << "  --tokens    Print lexical tokens\n"
                      << "  --ir        Print three-address intermediate representation\n"
                      << "  --optimize  Apply constant folding before evaluation\n"
                      << "  --all       Show tokens, optimization, IR and result\n";
            return 0;
        } else { if (!expression.empty()) expression += " "; expression += arg; }
    }
    if (expression.empty()) { std::cerr << "Usage: minicompiler [options] \"EXPRESSION\"\n"; return 2; }
    try {
        if (all || showTokens) printTokens(expression);
        Parser parser(expression);
        auto tree = parser.parse();
        if (all || doOptimize) {
            tree = optimize(std::move(tree));
            if (all) std::cout << "OPTIMIZATION: constant folding applied where safe\n";
        }
        if (all || showIR) {
            std::vector<std::string> lines; int temp = 0;
            std::string result = emitIR(*tree, lines, temp);
            std::cout << "THREE-ADDRESS IR:\n";
            for (const auto& line : lines) std::cout << "  " << line << "\n";
            std::cout << "  RESULT = " << result << "\n";
        }
        long long result = eval(*tree);
        if (resultOnly) std::cout << result << "\n";
        else std::cout << "RESULT: " << result << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
